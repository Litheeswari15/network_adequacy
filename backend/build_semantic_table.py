import os
import json
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\network_adequacy"

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset"
)

PATIENT_FILE = os.path.join(
    DATASET_DIR,
    "Patient_Dataset.xlsx"
)

PROVIDER_FILE = os.path.join(
    DATASET_DIR,
    "Provider_Dataset.xlsx"
)

CAPACITY_FILE = os.path.join(
    DATASET_DIR,
    "capacity count.csv"
)

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "Capacity_Adequacy",
    "config",
    "capacity_config.json"
)

OUTPUT_FILE = os.path.join(
    DATASET_DIR,
    "semantic_table.csv"
)


# ============================================================
# CHECK FILES
# ============================================================

required_files = [
    PATIENT_FILE,
    PROVIDER_FILE,
    CAPACITY_FILE,
    CONFIG_FILE
]

for file_path in required_files:

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"\nFile not found:\n{file_path}"
        )


# ============================================================
# LOAD DATA
# ============================================================

print("Loading Patient_Dataset.xlsx...")

patients = pd.read_excel(
    PATIENT_FILE
)


print("Loading Provider_Dataset.xlsx...")

providers = pd.read_excel(
    PROVIDER_FILE
)


print("Loading capacity count.csv...")

capacity_rules = pd.read_csv(
    CAPACITY_FILE
)


print("Loading capacity_config.json...")

with open(
    CONFIG_FILE,
    "r",
    encoding="utf-8"
) as file:

    config = json.load(file)


# ============================================================
# CAPACITY CONFIG
# ============================================================

specialty_capacity = config.get(
    "specialty_capacity",
    {}
)


print("\nSpecialist capacities:")

for specialist, capacity in specialty_capacity.items():

    print(
        f"  {specialist}: {capacity}"
    )


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

patients.columns = (
    patients.columns
    .astype(str)
    .str.strip()
)

providers.columns = (
    providers.columns
    .astype(str)
    .str.strip()
)

capacity_rules.columns = (
    capacity_rules.columns
    .astype(str)
    .str.strip()
)


# ============================================================
# PRINT COLUMNS
# ============================================================

print("\nPatient columns:")
print(
    list(patients.columns)
)

print("\nProvider columns:")
print(
    list(providers.columns)
)

print("\nCapacity-rule columns:")
print(
    list(capacity_rules.columns)
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):

    if pd.isna(value):

        return ""

    return (
        str(value)
        .strip()
        .upper()
    )


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

patient_required = [
    "County",
    "City/Town",
    "Specialist",
    "Latitude",
    "Longitude"
]

provider_required = [
    "County",
    "City/Town",
    "Specialty",
    "Latitude",
    "Longitude"
]

capacity_required = [
    "County",
    "City/Town",
    "Specialist",
    "Maximum_Distance_Miles"
]


for column in patient_required:

    if column not in patients.columns:

        raise ValueError(
            f"Patient dataset missing column: {column}"
        )


for column in provider_required:

    if column not in providers.columns:

        raise ValueError(
            f"Provider dataset missing column: {column}"
        )


for column in capacity_required:

    if column not in capacity_rules.columns:

        raise ValueError(
            f"Capacity count.csv missing column: {column}"
        )


# ============================================================
# NORMALIZED COLUMNS
# ============================================================

patients["_county"] = (
    patients["County"]
    .apply(normalize)
)

patients["_city"] = (
    patients["City/Town"]
    .apply(normalize)
)

patients["_specialist"] = (
    patients["Specialist"]
    .apply(normalize)
)


providers["_county"] = (
    providers["County"]
    .apply(normalize)
)

providers["_city"] = (
    providers["City/Town"]
    .apply(normalize)
)

providers["_specialist"] = (
    providers["Specialty"]
    .apply(normalize)
)


capacity_rules["_county"] = (
    capacity_rules["County"]
    .apply(normalize)
)

capacity_rules["_city"] = (
    capacity_rules["City/Town"]
    .apply(normalize)
)

capacity_rules["_specialist"] = (
    capacity_rules["Specialist"]
    .apply(normalize)
)


# ============================================================
# SPECIALIST CAPACITY LOOKUP
# ============================================================

capacity_lookup = {}

for specialist, capacity in specialty_capacity.items():

    capacity_lookup[
        normalize(specialist)
    ] = float(capacity)


# ============================================================
# BUILD VALID COUNTY/CITY/SPECIALIST COMBINATIONS
# ============================================================

# We use the capacity count table as the source of
# valid County + City/Town + Specialist combinations.

combinations = (
    capacity_rules[
        [
            "_county",
            "_city",
            "_specialist"
        ]
    ]
    .drop_duplicates()
    .copy()
)


print(
    f"\nTotal combinations to calculate: "
    f"{len(combinations)}"
)


# ============================================================
# EARTH RADIUS
# ============================================================

EARTH_RADIUS_MILES = 3958.7613


# ============================================================
# CREATE OUTPUT
# ============================================================

rows = []


# ============================================================
# PROCESS EVERY COMBINATION
# ============================================================

for index, combination in combinations.iterrows():

    county = combination["_county"]

    city = combination["_city"]

    specialist = combination["_specialist"]


    print(
        f"\rProcessing "
        f"{index + 1}/{len(combinations)} "
        f"| {county} | {city} | {specialist}",
        end=""
    )


    # ========================================================
    # PATIENT FILTER
    #
    # County + City/Town + Specialist
    # ========================================================

    filtered_patients = patients[
        (
            patients["_county"]
            == county
        )
        &
        (
            patients["_city"]
            == city
        )
        &
        (
            patients["_specialist"]
            == specialist
        )
    ].copy()


    # ========================================================
    # PROVIDER FILTER
    #
    # County + City/Town + Specialist
    # ========================================================

    filtered_providers = providers[
        (
            providers["_county"]
            == county
        )
        &
        (
            providers["_city"]
            == city
        )
        &
        (
            providers["_specialist"]
            == specialist
        )
    ].copy()


    # ========================================================
    # COUNTS
    # ========================================================

    patient_count = len(
        filtered_patients
    )

    provider_count = len(
        filtered_providers
    )


    # ========================================================
    # CAPACITY PER PROVIDER
    #
    # Taken ONLY from capacity_config.json
    # based on specialist.
    # ========================================================

    capacity_per_provider = (
        capacity_lookup.get(
            specialist,
            0
        )
    )


    # ========================================================
    # SUPPORT
    #
    # support =
    # capacity per provider × provider count
    # ========================================================

    support = (
        capacity_per_provider
        *
        provider_count
    )


    # ========================================================
    # CAPACITY ADEQUACY
    #
    # support / patients × 100
    # ========================================================

    if patient_count > 0:

        capacity_adequacy = (
            support
            /
            patient_count
        ) * 100

    else:

        capacity_adequacy = 0


    # ========================================================
    # MAXIMUM DISTANCE
    # ========================================================

    distance_rule = capacity_rules[
        (
            capacity_rules["_county"]
            == county
        )
        &
        (
            capacity_rules["_city"]
            == city
        )
        &
        (
            capacity_rules["_specialist"]
            == specialist
        )
    ]


    if distance_rule.empty:

        maximum_distance = 0

    else:

        maximum_distance = float(
            distance_rule.iloc[0][
                "Maximum_Distance_Miles"
            ]
        )


    # ========================================================
    # DISTANCE ADEQUACY
    #
    # Find nearest provider for every patient.
    # ========================================================

    patients_with_coordinates = (
        filtered_patients[
            [
                "Latitude",
                "Longitude"
            ]
        ]
        .dropna()
        .copy()
    )


    providers_with_coordinates = (
        filtered_providers[
            [
                "Latitude",
                "Longitude"
            ]
        ]
        .dropna()
        .copy()
    )


    if (
        len(patients_with_coordinates) > 0
        and
        len(providers_with_coordinates) > 0
    ):

        # ----------------------------------------------------
        # Convert coordinates to radians
        # ----------------------------------------------------

        patient_coordinates = np.deg2rad(
            patients_with_coordinates[
                [
                    "Latitude",
                    "Longitude"
                ]
            ]
            .astype(float)
            .to_numpy()
        )


        provider_coordinates = np.deg2rad(
            providers_with_coordinates[
                [
                    "Latitude",
                    "Longitude"
                ]
            ]
            .astype(float)
            .to_numpy()
        )


        # ----------------------------------------------------
        # BallTree
        # ----------------------------------------------------

        tree = BallTree(
            provider_coordinates,
            metric="haversine"
        )


        distances, indices = tree.query(
            patient_coordinates,
            k=1
        )


        # ----------------------------------------------------
        # Convert radians to miles
        # ----------------------------------------------------

        nearest_distances = (
            distances[:, 0]
            *
            EARTH_RADIUS_MILES
        )


        # ----------------------------------------------------
        # Patients within maximum distance
        # ----------------------------------------------------

        reasonable_patients = int(
            (
                nearest_distances
                <= maximum_distance
            )
            .sum()
        )


        distance_patient_count = len(
            patients_with_coordinates
        )


    else:

        reasonable_patients = 0

        distance_patient_count = 0


    # ========================================================
    # DISTANCE ADEQUACY
    # ========================================================

    if distance_patient_count > 0:

        distance_adequacy = (
            reasonable_patients
            /
            distance_patient_count
        ) * 100

    else:

        distance_adequacy = 0


    # ========================================================
    # TOTAL ADEQUACY
    #
    # total =
    # (capacity + distance) / 2
    # ========================================================

    total_adequacy = (
        capacity_adequacy
        +
        distance_adequacy
    ) / 2


    # ========================================================
    # STATUS
    # ========================================================

    if total_adequacy >= 90:

        status = "HIGHLY ADEQUATE"

    elif total_adequacy >= 75:

        status = "ADEQUATE"

    elif total_adequacy >= 50:

        status = "PARTIALLY ADEQUATE"

    else:

        status = "INADEQUATE"


    # ========================================================
    # STORE ROW
    # ========================================================

    rows.append({

        "county":
            str(
                capacity_rules.loc[
                    index,
                    "County"
                ]
            ).strip(),

        "city_town":
            str(
                capacity_rules.loc[
                    index,
                    "City/Town"
                ]
            ).strip(),

        "specialist":
            str(
                capacity_rules.loc[
                    index,
                    "Specialist"
                ]
            ).strip(),

        "patient_count":
            patient_count,

        "provider_count":
            provider_count,

        "capacity_per_provider":
            capacity_per_provider,

        "support":
            support,

        "capacity_adequacy":
            round(
                capacity_adequacy,
                2
            ),

        "maximum_distance":
            maximum_distance,

        "reasonable_patients":
            reasonable_patients,

        "distance_adequacy":
            round(
                distance_adequacy,
                2
            ),

        "total_adequacy":
            round(
                total_adequacy,
                2
            ),

        "status":
            status
    })


# ============================================================
# CREATE DATAFRAME
# ============================================================

semantic_table = pd.DataFrame(
    rows
)


# ============================================================
# EXACT COLUMN ORDER
# ============================================================

semantic_table = semantic_table[
    [
        "county",
        "city_town",
        "specialist",
        "patient_count",
        "provider_count",
        "capacity_per_provider",
        "support",
        "capacity_adequacy",
        "maximum_distance",
        "reasonable_patients",
        "distance_adequacy",
        "total_adequacy",
        "status"
    ]
]


# ============================================================
# SAVE CSV
# ============================================================

semantic_table.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINISHED
# ============================================================

print("\n\n")
print("=" * 60)
print("SEMANTIC TABLE CREATED SUCCESSFULLY")
print("=" * 60)

print(
    f"Rows created: {len(semantic_table)}"
)

print(
    f"Output file:"
)

print(
    OUTPUT_FILE
)

print("=" * 60)
