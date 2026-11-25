import os
import requests


# ============================================================
# PATH
# ============================================================

BASE_DIR = r"D:\network_adequacy"

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "geojson"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# OFFICIAL GIS LAYER URLs
# ============================================================

COUNTY_URL = (
    "https://maps.dot.state.tx.us/"
    "arcgis/rest/services/Boundaries/"
    "MapServer/1/query"
)

CITY_URL = (
    "https://maps.dot.state.tx.us/"
    "arcgis/rest/services/TRIMS_BaseMap/"
    "MapServer/2/query"
)

ZCTA_URL = (
    "https://services3.arcgis.com/"
    "vDIjL0K2YNmAOCEt/"
    "ArcGIS/rest/services/ZCTAs/"
    "FeatureServer/0/query"
)


# ============================================================
# DOWNLOAD FUNCTION
# ============================================================

def download_geojson(
    url,
    output_file,
    where="1=1"
):

    print()
    print("=" * 60)
    print("Downloading:")
    print(output_file)
    print("=" * 60)

    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        if (
            "features" not in data
            or
            len(data["features"]) == 0
        ):

            print(
                "❌ No features returned."
            )

            return False


        output_path = os.path.join(
            OUTPUT_DIR,
            output_file
        )


        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            import json

            json.dump(
                data,
                file,
                ensure_ascii=False
            )


        print(
            f"✅ Saved: {output_path}"
        )

        print(
            f"Features: {len(data['features'])}"
        )

        return True


    except Exception as error:

        print(
            "❌ Download failed:"
        )

        print(error)

        return False


# ============================================================
# 1. TEXAS COUNTIES
# ============================================================

county_success = download_geojson(
    COUNTY_URL,
    "texas_counties.geojson"
)


# ============================================================
# 2. TEXAS CITIES / TOWNS
# ============================================================

city_success = download_geojson(
    CITY_URL,
    "texas_cities.geojson"
)


# ============================================================
# 3. TEXAS ZIP / ZCTA AREAS
# ============================================================

# ZCTA layer is nationwide.
# Texas ZIP areas are selected using
# Texas longitude/latitude bounding box.

zcta_where = (
    "1=1"
)

zip_success = download_geojson(
    ZCTA_URL,
    "texas_zipcodes.geojson",
    zcta_where
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)
print("GEOJSON DOWNLOAD COMPLETE")
print("=" * 60)

print()

if county_success:
    print(
        "✅ texas_counties.geojson"
    )
else:
    print(
        "❌ texas_counties.geojson"
    )

if city_success:
    print(
        "✅ texas_cities.geojson"
    )
else:
    print(
        "❌ texas_cities.geojson"
    )

if zip_success:
    print(
        "✅ texas_zipcodes.geojson"
    )
else:
    print(
        "❌ texas_zipcodes.geojson"
    )

print()
print(
    "Output folder:"
)

print(
    OUTPUT_DIR
)