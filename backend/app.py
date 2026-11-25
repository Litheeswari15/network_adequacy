from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import pandas as pd
import os
import json
import math


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="CareNet Network Adequacy API",
    description="Backend API for CareNet Provider Network Adequacy",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PROJECT PATHS
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

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "Capacity_Adequacy",
    "config",
    "capacity_config.json"
)

CAPACITY_FILE = os.path.join(
    DATASET_DIR,
    "capacity_count.csv"
)


# ============================================================
# LOAD CONFIG
# ============================================================

def load_capacity_config():

    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(
            f"Capacity config not found:\n{CONFIG_FILE}"
        )

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        config = json.load(file)

    return config


def get_capacity_per_provider(
    specialist: Optional[str]
):

    config = load_capacity_config()

    specialty_capacity = config.get(
        "specialty_capacity",
        {}
    )

    # No specialist selected
    if not specialist:
        return None

    specialist_clean = str(
        specialist
    ).strip()

    # Direct match
    if specialist_clean in specialty_capacity:

        return float(
            specialty_capacity[
                specialist_clean
            ]
        )

    # Case-insensitive match
    for name, value in specialty_capacity.items():

        if str(name).strip().lower() == specialist_clean.lower():

            return float(value)

    return None


# ============================================================
# LOAD DATASETS
# ============================================================

def load_patient_data():

    if not os.path.exists(PATIENT_FILE):

        raise FileNotFoundError(
            f"Patient dataset not found:\n{PATIENT_FILE}"
        )

    df = pd.read_excel(
        PATIENT_FILE
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


def load_provider_data():

    if not os.path.exists(PROVIDER_FILE):

        raise FileNotFoundError(
            f"Provider dataset not found:\n{PROVIDER_FILE}"
        )

    df = pd.read_excel(
        PROVIDER_FILE
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# ============================================================
# LOAD DATA
# ============================================================

try:

    patients = load_patient_data()

except Exception as error:

    print(
        "Patient dataset error:",
        error
    )

    patients = pd.DataFrame()


try:

    providers = load_provider_data()

except Exception as error:

    print(
        "Provider dataset error:",
        error
    )

    providers = pd.DataFrame()


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

def normalize_columns(df):

    if df.empty:
        return df

    df = df.copy()

    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        for column in df.columns
    ]

    return df


patients = normalize_columns(
    patients
)

providers = normalize_columns(
    providers
)


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    if value.lower() in [
        "all",
        "none",
        "null",
        "undefined"
    ]:
        return None

    return value


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(
    df,
    possible_names
):

    if df.empty:
        return None

    columns = set(
        df.columns
    )

    normalized_possible = []

    for name in possible_names:

        normalized = (
            str(name)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
        )

        normalized_possible.append(
            normalized
        )

        if normalized in columns:
            return normalized

    # City/Town support
    if (
        "city_town" in columns
        and any(
            name in normalized_possible
            for name in [
                "city",
                "city_name",
                "town",
                "town_name"
            ]
        )
    ):
        return "city_town"

    return None


# ============================================================
# COLUMN DEFINITIONS
# ============================================================

COUNTY_COLUMNS = [
    "county",
    "county_name",
    "cnty_nm"
]

CITY_COLUMNS = [
    "city",
    "city_name",
    "town",
    "town_name",
    "city_town"
]

ZIP_COLUMNS = [
    "zipcode",
    "zip_code",
    "zip",
    "postal_code"
]

PATIENT_SPECIALTY_COLUMNS = [
    "specialist",
    "specialty",
    "specialization"
]

PROVIDER_SPECIALTY_COLUMNS = [
    "specialist",
    "specialty",
    "specialization",
    "provider_specialty",
    "pri_spec",
    "primary_specialty"
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text_series(series):

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


def normalize_zip_series(series):

    return (
        series
        .fillna("")
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False
        )
        .str.strip()
    )


# ============================================================
# FILTER DATA
# ============================================================

def apply_filters(
    df,
    county=None,
    city=None,
    specialist=None,
    zipcode=None,
    apply_specialist=True
):

    if df.empty:
        return df.copy()

    result = df.copy()

    county = clean_value(
        county
    )

    city = clean_value(
        city
    )

    specialist = clean_value(
        specialist
    )

    zipcode = clean_value(
        zipcode
    )

    # --------------------------------------------------------
    # COUNTY
    # --------------------------------------------------------

    if county:

        column = find_column(
            result,
            COUNTY_COLUMNS
        )

        if column:

            result = result[
                normalize_text_series(
                    result[column]
                )
                ==
                county.strip().upper()
            ]


    # --------------------------------------------------------
    # CITY / TOWN
    # --------------------------------------------------------

    if city:

        column = find_column(
            result,
            CITY_COLUMNS
        )

        if column:

            result = result[
                normalize_text_series(
                    result[column]
                )
                ==
                city.strip().upper()
            ]


    # --------------------------------------------------------
    # ZIP CODE
    # --------------------------------------------------------

    if zipcode:

        column = find_column(
            result,
            ZIP_COLUMNS
        )

        if column:

            result = result[
                normalize_zip_series(
                    result[column]
                )
                ==
                normalize_zip_series(
                    pd.Series([zipcode])
                ).iloc[0]
            ]


    # --------------------------------------------------------
    # SPECIALIST
    # --------------------------------------------------------

    if specialist and apply_specialist:

        column = find_column(
            result,
            PROVIDER_SPECIALTY_COLUMNS
        )

        if column:

            result = result[
                normalize_text_series(
                    result[column]
                )
                ==
                specialist.strip().upper()
            ]

    return result


# ============================================================
# CAPACITY ADEQUACY
# ============================================================

def calculate_capacity_adequacy(
    patient_count,
    provider_count,
    capacity_per_provider
):

    patient_count = int(
        patient_count
    )

    provider_count = int(
        provider_count
    )

    capacity_per_provider = float(
        capacity_per_provider
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if patient_count < 0:

        raise ValueError(
            "Patient count cannot be negative."
        )

    if provider_count < 0:

        raise ValueError(
            "Provider count cannot be negative."
        )

    if capacity_per_provider <= 0:

        raise ValueError(
            "Capacity per provider must be greater than zero."
        )


    # --------------------------------------------------------
    # NO PATIENTS
    # --------------------------------------------------------

    if patient_count == 0:

        return 0.0


    # --------------------------------------------------------
    # SUPPORT
    #
    # support =
    # capacity_per_provider *
    # total_number_of_providers
    # --------------------------------------------------------

    support = (
        capacity_per_provider
        *
        provider_count
    )


    # --------------------------------------------------------
    # CAPACITY ADEQUACY
    #
    # capacity adequacy =
    # support / total patients * 100
    # --------------------------------------------------------

    capacity_adequacy = (
        support
        /
        patient_count
    ) * 100


    # Maximum 100%
    capacity_adequacy = min(
        capacity_adequacy,
        100.0
    )


    return round(
        capacity_adequacy,
        2
    )


# ============================================================
# DISTANCE ADEQUACY
# ============================================================

def calculate_distance_adequacy(
    patient_count,
    provider_count
):

    if patient_count <= 0:
        return 0.0

    if provider_count <= 0:
        return 0.0

    ratio = (
        provider_count
        /
        patient_count
    )

    score = min(
        ratio * 100,
        100
    )

    return round(
        score,
        2
    )


# ============================================================
# TOTAL ADEQUACY
# ============================================================

def calculate_total_adequacy(
    capacity_adequacy,
    distance_adequacy
):

    return round(
        (
            capacity_adequacy
            +
            distance_adequacy
        ) / 2,
        2
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "healthy",

        "patients_loaded":
            len(patients),

        "providers_loaded":
            len(providers),

        "config_loaded":
            os.path.exists(CONFIG_FILE)

    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "application":
            "CareNet Network Adequacy API",

        "status":
            "running",

        "version":
            "1.0.0",

        "endpoints": [

            "/api/health",

            "/api/config",

            "/api/filters",

            "/api/cities",

            "/api/zipcodes",

            "/api/adequacy",

            "/api/map-adequacy",

            "/api/summary"

        ]

    }


# ============================================================
# CONFIG
# ============================================================

@app.get("/api/config")
def get_config():

    config = load_capacity_config()

    return {

        "specialty_capacity":
            config.get(
                "specialty_capacity",
                {}
            ),

        "thresholds": {

            "high": 75,

            "moderate": 50,

            "low": 0

        }

    }


# ============================================================
# FILTERS
# ============================================================

@app.get("/api/filters")
def get_filters():

    response = {}

    # --------------------------------------------------------
    # COUNTIES
    # --------------------------------------------------------

    county_values = set()

    patient_county_column = find_column(
        patients,
        COUNTY_COLUMNS
    )

    provider_county_column = find_column(
        providers,
        COUNTY_COLUMNS
    )

    if patient_county_column:

        county_values.update(
            patients[
                patient_county_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    if provider_county_column:

        county_values.update(
            providers[
                provider_county_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    response["counties"] = sorted(
        [
            value
            for value in county_values
            if value
        ]
    )


    # --------------------------------------------------------
    # CITIES
    # --------------------------------------------------------

    city_values = set()

    patient_city_column = find_column(
        patients,
        CITY_COLUMNS
    )

    provider_city_column = find_column(
        providers,
        CITY_COLUMNS
    )

    if patient_city_column:

        city_values.update(
            patients[
                patient_city_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    if provider_city_column:

        city_values.update(
            providers[
                provider_city_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    response["cities"] = sorted(
        [
            value
            for value in city_values
            if value
        ]
    )


    # --------------------------------------------------------
    # SPECIALISTS
    # --------------------------------------------------------

    specialist_values = set()

    provider_specialty_column = find_column(
        providers,
        PROVIDER_SPECIALTY_COLUMNS
    )

    if provider_specialty_column:

        specialist_values.update(
            providers[
                provider_specialty_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    # Also read specialties from JSON
    try:

        config = load_capacity_config()

        specialist_values.update(
            config
            .get(
                "specialty_capacity",
                {}
            )
            .keys()
        )

    except Exception:
        pass

    response["specialists"] = sorted(
        [
            value
            for value in specialist_values
            if value
        ]
    )

    return response


# ============================================================
# CITIES
# ============================================================

@app.get("/api/cities")
def get_cities(
    county: Optional[str] = Query(None)
):

    patient_data = apply_filters(
        patients,
        county=county,
        apply_specialist=False
    )

    provider_data = apply_filters(
        providers,
        county=county,
        apply_specialist=False
    )

    cities = set()

    patient_city_column = find_column(
        patient_data,
        CITY_COLUMNS
    )

    provider_city_column = find_column(
        provider_data,
        CITY_COLUMNS
    )

    if patient_city_column:

        cities.update(
            patient_data[
                patient_city_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    if provider_city_column:

        cities.update(
            provider_data[
                provider_city_column
            ]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    return sorted(
        [
            city
            for city in cities
            if city
        ]
    )


# ============================================================
# ZIP CODES
# ============================================================

@app.get("/api/zipcodes")
def get_zipcodes(
    county: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):

    patient_data = apply_filters(
        patients,
        county=county,
        city=city,
        apply_specialist=False
    )

    provider_data = apply_filters(
        providers,
        county=county,
        city=city,
        apply_specialist=False
    )

    zipcodes = set()

    patient_zip_column = find_column(
        patient_data,
        ZIP_COLUMNS
    )

    provider_zip_column = find_column(
        provider_data,
        ZIP_COLUMNS
    )

    if patient_zip_column:

        zipcodes.update(
            normalize_zip_series(
                patient_data[
                    patient_zip_column
                ]
            )
            .tolist()
        )

    if provider_zip_column:

        zipcodes.update(
            normalize_zip_series(
                provider_data[
                    provider_zip_column
                ]
            )
            .tolist()
        )

    return sorted(
        [
            zipcode
            for zipcode in zipcodes
            if zipcode
        ]
    )


# ============================================================
# ADEQUACY
# ============================================================

@app.get("/api/adequacy")
def get_adequacy(

    county: Optional[str] = Query(None),

    city: Optional[str] = Query(None),

    specialist: Optional[str] = Query(None),

    zipcode: Optional[str] = Query(None)

):

    county = clean_value(
        county
    )

    city = clean_value(
        city
    )

    specialist = clean_value(
        specialist
    )

    zipcode = clean_value(
        zipcode
    )


    # --------------------------------------------------------
    # SPECIALIST CAPACITY
    # --------------------------------------------------------

    if not specialist:

        raise ValueError(
            "Specialist is required for capacity adequacy."
        )


    capacity_per_provider = (
        get_capacity_per_provider(
            specialist
        )
    )


    if capacity_per_provider is None:

        raise ValueError(
            f"No capacity configured for specialist: {specialist}"
        )


    # ========================================================
    # PATIENT FILTER
    #
    # IMPORTANT:
    # Patient count DOES NOT use specialist filter.
    #
    # Patients are filtered by:
    # county
    # city
    # zipcode
    # ========================================================

    filtered_patients = apply_filters(

        patients,

        county=county,

        city=city,

        zipcode=zipcode,

        apply_specialist=False

    )


    # ========================================================
    # PROVIDER FILTER
    #
    # Provider count uses:
    # county
    # city
    # zipcode
    # specialist
    # ========================================================

    filtered_providers = apply_filters(

        providers,

        county=county,

        city=city,

        zipcode=zipcode,

        specialist=specialist,

        apply_specialist=True

    )


    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    patient_count = len(
        filtered_patients
    )

    provider_count = len(
        filtered_providers
    )


    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    support = (
        capacity_per_provider
        *
        provider_count
    )


    # --------------------------------------------------------
    # CAPACITY ADEQUACY
    # --------------------------------------------------------

    capacity_adequacy = (
        calculate_capacity_adequacy(

            patient_count,

            provider_count,

            capacity_per_provider

        )
    )


    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    distance_adequacy = (
        calculate_distance_adequacy(

            patient_count,

            provider_count

        )
    )


    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_adequacy = (
        calculate_total_adequacy(

            capacity_adequacy,

            distance_adequacy

        )
    )


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "filters": {

            "county":
                county,

            "city":
                city,

            "specialist":
                specialist,

            "zipcode":
                zipcode

        },

        "patients":
            patient_count,

        "providers":
            provider_count,

        "capacity_per_provider":
            capacity_per_provider,

        "support":
            support,

        "capacity_adequacy":
            capacity_adequacy,

        "distance_adequacy":
            distance_adequacy,

        "total_adequacy":
            total_adequacy

    }


# ============================================================
# MAP ADEQUACY
# ============================================================

@app.get("/api/map-adequacy")
def get_map_adequacy(

    county: Optional[str] = Query(None),

    city: Optional[str] = Query(None),

    specialist: Optional[str] = Query(None)

):

    county = clean_value(
        county
    )

    city = clean_value(
        city
    )

    specialist = clean_value(
        specialist
    )


    if not specialist:

        raise ValueError(
            "Specialist is required for map adequacy."
        )


    capacity_per_provider = (
        get_capacity_per_provider(
            specialist
        )
    )


    if capacity_per_provider is None:

        raise ValueError(
            f"No capacity configured for specialist: {specialist}"
        )


    # ========================================================
    # PATIENTS
    # ========================================================

    filtered_patients = apply_filters(

        patients,

        county=county,

        city=city,

        apply_specialist=False

    )


    # ========================================================
    # PROVIDERS
    # ========================================================

    filtered_providers = apply_filters(

        providers,

        county=county,

        city=city,

        specialist=specialist,

        apply_specialist=True

    )


    results = []


    # ========================================================
    # COLUMN IDENTIFICATION
    # ========================================================

    patient_county_column = find_column(
        filtered_patients,
        COUNTY_COLUMNS
    )

    patient_city_column = find_column(
        filtered_patients,
        CITY_COLUMNS
    )

    patient_zip_column = find_column(
        filtered_patients,
        ZIP_COLUMNS
    )


    # ========================================================
    # COUNTY LEVEL
    # ========================================================

    if patient_county_column:

        county_groups = (

            filtered_patients

            .groupby(
                patient_county_column
            )

            .size()

            .reset_index(
                name="patients"
            )

        )

        for _, row in county_groups.iterrows():

            county_name = str(
                row[
                    patient_county_column
                ]
            ).strip()

            patient_count = int(
                row["patients"]
            )


            provider_subset = apply_filters(

                filtered_providers,

                county=county_name,

                apply_specialist=True

            )


            provider_count = len(
                provider_subset
            )


            capacity = (
                calculate_capacity_adequacy(

                    patient_count,

                    provider_count,

                    capacity_per_provider

                )
            )


            distance = (
                calculate_distance_adequacy(

                    patient_count,

                    provider_count

                )
            )


            total = (
                calculate_total_adequacy(

                    capacity,

                    distance

                )
            )


            results.append({

                "level":
                    "county",

                "county":
                    county_name,

                "city":
                    None,

                "zipcode":
                    None,

                "patients":
                    patient_count,

                "providers":
                    provider_count,

                "capacity_per_provider":
                    capacity_per_provider,

                "capacity_adequacy":
                    capacity,

                "distance_adequacy":
                    distance,

                "total_adequacy":
                    total

            })


    # ========================================================
    # CITY LEVEL
    # ========================================================

    if (
        patient_county_column
        and
        patient_city_column
    ):

        city_groups = (

            filtered_patients

            .groupby(
                [
                    patient_county_column,
                    patient_city_column
                ]
            )

            .size()

            .reset_index(
                name="patients"
            )

        )


        for _, row in city_groups.iterrows():

            county_name = str(
                row[
                    patient_county_column
                ]
            ).strip()

            city_name = str(
                row[
                    patient_city_column
                ]
            ).strip()

            patient_count = int(
                row["patients"]
            )


            provider_subset = apply_filters(

                filtered_providers,

                county=county_name,

                city=city_name,

                apply_specialist=True

            )


            provider_count = len(
                provider_subset
            )


            capacity = (
                calculate_capacity_adequacy(

                    patient_count,

                    provider_count,

                    capacity_per_provider

                )
            )


            distance = (
                calculate_distance_adequacy(

                    patient_count,

                    provider_count

                )
            )


            total = (
                calculate_total_adequacy(

                    capacity,

                    distance

                )
            )


            results.append({

                "level":
                    "city",

                "county":
                    county_name,

                "city":
                    city_name,

                "zipcode":
                    None,

                "patients":
                    patient_count,

                "providers":
                    provider_count,

                "capacity_per_provider":
                    capacity_per_provider,

                "capacity_adequacy":
                    capacity,

                "distance_adequacy":
                    distance,

                "total_adequacy":
                    total

            })


    # ========================================================
    # ZIP CODE LEVEL
    # ========================================================

    if (
        patient_county_column
        and
        patient_city_column
        and
        patient_zip_column
    ):

        zip_groups = (

            filtered_patients

            .groupby(
                [
                    patient_county_column,
                    patient_city_column,
                    patient_zip_column
                ]
            )

            .size()

            .reset_index(
                name="patients"
            )

        )


        for _, row in zip_groups.iterrows():

            county_name = str(
                row[
                    patient_county_column
                ]
            ).strip()

            city_name = str(
                row[
                    patient_city_column
                ]
            ).strip()

            zipcode_name = str(
                row[
                    patient_zip_column
                ]
            )

            if zipcode_name.endswith(
                ".0"
            ):

                zipcode_name = (
                    zipcode_name[:-2]
                )

            zipcode_name = (
                zipcode_name.strip()
            )


            patient_count = int(
                row["patients"]
            )


            provider_subset = apply_filters(

                filtered_providers,

                county=county_name,

                city=city_name,

                zipcode=zipcode_name,

                apply_specialist=True

            )


            provider_count = len(
                provider_subset
            )


            capacity = (
                calculate_capacity_adequacy(

                    patient_count,

                    provider_count,

                    capacity_per_provider

                )
            )


            distance = (
                calculate_distance_adequacy(

                    patient_count,

                    provider_count

                )
            )


            total = (
                calculate_total_adequacy(

                    capacity,

                    distance

                )
            )


            results.append({

                "level":
                    "zipcode",

                "county":
                    county_name,

                "city":
                    city_name,

                "zipcode":
                    zipcode_name,

                "patients":
                    patient_count,

                "providers":
                    provider_count,

                "capacity_per_provider":
                    capacity_per_provider,

                "capacity_adequacy":
                    capacity,

                "distance_adequacy":
                    distance,

                "total_adequacy":
                    total

            })


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "filters": {

            "county":
                county,

            "city":
                city,

            "specialist":
                specialist

        },

        "capacity_per_provider":
            capacity_per_provider,

        "data":
            results

    }


# ============================================================
# SUMMARY
# ============================================================

@app.get("/api/summary")
def get_summary(

    county: Optional[str] = Query(None),

    city: Optional[str] = Query(None),

    specialist: Optional[str] = Query(None),

    zipcode: Optional[str] = Query(None)

):

    result = get_adequacy(

        county=county,

        city=city,

        specialist=specialist,

        zipcode=zipcode

    )


    return {

        "patients":
            result["patients"],

        "providers":
            result["providers"],

        "capacity_per_provider":
            result["capacity_per_provider"],

        "support":
            result["support"],

        "capacity_adequacy":
            result["capacity_adequacy"],

        "distance_adequacy":
            result["distance_adequacy"],

        "total_adequacy":
            result["total_adequacy"]

    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "app:app",

        host="127.0.0.1",

        port=8000,

        reload=True

    )

    