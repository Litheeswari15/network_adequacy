"""
CareNet Frontend
----------------
Frontend is ONLY for:
    1. Selecting filters
    2. Fetching data from FastAPI
    3. Displaying the values

IMPORTANT:
    No Patient/Provider Excel files are loaded here.
    No adequacy calculations are performed here.

All adequacy values come from:

    semantic_table.csv
            ↓
       backend/app.py
            ↓
       Frontend/app.py
"""

import streamlit as st
import json
import logging

from urllib.request import urlopen
from urllib.parse import urlencode


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CareNet Network Adequacy",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# BACKEND URL
# ============================================================

API_BASE_URL = st.session_state.get(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# GENERIC BACKEND GET
# ============================================================

def backend_get(endpoint, params=None, timeout=10):
    """
    Sends a GET request to the FastAPI backend.

    Frontend does not calculate anything.
    It only receives data from backend.
    """

    try:

        url = f"{API_BASE_URL}{endpoint}"

        if params:

            clean_params = {}

            for key, value in params.items():

                if value is None:
                    continue

                if str(value).strip() == "":
                    continue

                if str(value).lower() == "all":
                    continue

                clean_params[key] = value

            if clean_params:

                url += "?" + urlencode(
                    clean_params
                )

        with urlopen(
            url,
            timeout=timeout
        ) as response:

            response_text = (
                response
                .read()
                .decode("utf-8")
            )

            return (
                json.loads(response_text),
                None
            )

    except Exception as error:

        logger.error(
            f"Backend request failed: {error}"
        )

        return (
            None,
            str(error)
        )


# ============================================================
# GET COUNTIES
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False
)
def fetch_counties():

    data, error = backend_get(
        "/api/counties"
    )

    if error:

        return [], error

    if not data:

        return [], "Empty response from backend."

    counties = data.get(
        "counties",
        []
    )

    return counties, None


# ============================================================
# GET CITIES
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False
)
def fetch_cities(county):

    data, error = backend_get(
        "/api/cities",
        {
            "county": county
        }
    )

    if error:

        return [], error

    if not data:

        return [], "Empty response from backend."

    cities = data.get(
        "cities",
        []
    )

    return cities, None


# ============================================================
# GET SPECIALISTS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False
)
def fetch_specialists(
    county,
    city
):

    params = {
        "county": county
    }

    if city != "All":

        params["city"] = city

    data, error = backend_get(
        "/api/specialists",
        params
    )

    if error:

        return [], error

    if not data:

        return [], "Empty response from backend."

    specialists = data.get(
        "specialists",
        []
    )

    return specialists, None


# ============================================================
# GET ADEQUACY
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False
)
def fetch_backend_adequacy(
    county,
    city,
    specialist
):
    """
    IMPORTANT:

    This function does NOT calculate:

        capacity_adequacy
        distance_adequacy
        total_adequacy

    It only asks the backend for them.

    Backend gets them directly from semantic_table.csv.
    """

    params = {
        "county": county,
        "specialist": specialist
    }

    if city != "All":

        params["city"] = city

    data, error = backend_get(
        "/api/adequacy",
        params,
        timeout=10
    )

    return data, error


# ============================================================
# PAGE TITLE
# ============================================================

st.title(
    "🏥 CareNet Network Adequacy Analysis"
)

st.markdown(
    "**Healthcare Provider Network Adequacy Assessment**"
)


# ============================================================
# FILTERS
# ============================================================

st.markdown("---")

st.subheader(
    "📊 Filters"
)


filter_col1, filter_col2, filter_col3 = st.columns(3)


# ============================================================
# COUNTY
# ============================================================

with filter_col1:

    counties, county_error = (
        fetch_counties()
    )

    if county_error:

        st.error(
            f"❌ Unable to load counties: "
            f"{county_error}"
        )

        st.stop()


    if not counties:

        st.warning(
            "No counties available."
        )

        st.stop()


    selected_county = st.selectbox(
        "📍 County",
        counties,
        key="county_filter"
    )


# ============================================================
# CITY / TOWN
# ============================================================

with filter_col2:

    cities, city_error = (
        fetch_cities(
            selected_county
        )
    )

    if city_error:

        st.error(
            f"❌ Unable to load cities: "
            f"{city_error}"
        )

        cities = []


    selected_city = st.selectbox(
        "🏙️ City / Town",
        ["All"] + cities,
        key="city_filter"
    )


# ============================================================
# SPECIALIST
# ============================================================

with filter_col3:

    specialists, specialist_error = (
        fetch_specialists(
            selected_county,
            selected_city
        )
    )

    if specialist_error:

        st.error(
            f"❌ Unable to load specialists: "
            f"{specialist_error}"
        )

        specialists = []


    if not specialists:

        st.warning(
            "No specialists available "
            "for the selected filters."
        )

        st.stop()


    selected_specialist = st.selectbox(
        "👨‍⚕️ Specialist",
        specialists,
        key="specialist_filter"
    )


# ============================================================
# FETCH SEMANTIC TABLE VALUES
# ============================================================

st.markdown("---")

st.subheader(
    "📈 Network Adequacy Metrics"
)


with st.spinner(
    "Fetching data from semantic table..."
):

    backend_data, backend_error = (
        fetch_backend_adequacy(
            selected_county,
            selected_city,
            selected_specialist
        )
    )


# ============================================================
# BACKEND ERROR
# ============================================================

if backend_error:

    st.error(
        f"❌ Backend Error: {backend_error}"
    )

    st.info(
        "Make sure the backend is running:\n\n"
        "`python -m uvicorn backend.app:app --reload`"
    )

    st.stop()


# ============================================================
# NO DATA
# ============================================================

if backend_data is None:

    st.warning(
        "⚠️ No data received from backend."
    )

    st.stop()


if not backend_data.get(
    "success",
    False
):

    st.warning(
        backend_data.get(
            "message",
            "No matching data found."
        )
    )

    st.stop()


# ============================================================
# EXTRACT VALUES FROM SEMANTIC TABLE
# ============================================================

"""
IMPORTANT:

These values are NOT calculated here.

They are directly returned by:

    backend/app.py

which reads:

    dataset/semantic_table.csv
"""

capacity_adequacy = float(
    backend_data.get(
        "capacity_adequacy",
        0
    )
)

distance_adequacy = float(
    backend_data.get(
        "distance_adequacy",
        0
    )
)

total_adequacy = float(
    backend_data.get(
        "total_adequacy",
        0
    )
)

patient_count = int(
    backend_data.get(
        "patient_count",
        0
    )
)

provider_count = int(
    backend_data.get(
        "provider_count",
        0
    )
)

capacity_per_provider = float(
    backend_data.get(
        "capacity_per_provider",
        0
    )
)

support = float(
    backend_data.get(
        "support",
        0
    )
)

maximum_distance = float(
    backend_data.get(
        "maximum_distance",
        0
    )
)

reasonable_patients = int(
    backend_data.get(
        "reasonable_patients",
        0
    )
)

status = backend_data.get(
    "status",
    "UNKNOWN"
)


# ============================================================
# METRIC CARDS
# ============================================================

card1, card2, card3 = st.columns(3)


with card1:

    st.metric(
        "Capacity Adequacy",
        f"{capacity_adequacy:.1f}%",
        delta=(
            f"{patient_count} patients, "
            f"{provider_count} providers"
        )
    )


with card2:

    st.metric(
        "Distance Adequacy",
        f"{distance_adequacy:.1f}%"
    )


with card3:

    st.metric(
        "Total Adequacy",
        f"{total_adequacy:.1f}%"
    )


# ============================================================
# DETAILED INFORMATION
# ============================================================

st.markdown("---")

st.subheader(
    "📋 Detailed Information"
)


info_col1, info_col2, info_col3, info_col4 = (
    st.columns(4)
)


with info_col1:

    st.info(
        f"👥 **Patients**\n\n"
        f"{patient_count}"
    )


with info_col2:

    st.info(
        f"⚕️ **Providers**\n\n"
        f"{provider_count}"
    )


with info_col3:

    st.info(
        f"📍 **County**\n\n"
        f"{selected_county}"
    )


with info_col4:

    st.info(
        f"👨‍⚕️ **Specialist**\n\n"
        f"{selected_specialist}"
    )


# ============================================================
# ADDITIONAL VALUES FROM SEMANTIC TABLE
# ============================================================

st.markdown("---")

st.subheader(
    "🔎 Backend Data"
)


detail_col1, detail_col2, detail_col3, detail_col4 = (
    st.columns(4)
)


with detail_col1:

    st.metric(
        "Capacity / Provider",
        f"{capacity_per_provider:.1f}"
    )


with detail_col2:

    st.metric(
        "Support",
        f"{support:.1f}"
    )


with detail_col3:

    st.metric(
        "Maximum Distance",
        f"{maximum_distance:.1f} miles"
    )


with detail_col4:

    st.metric(
        "Reasonable Patients",
        f"{reasonable_patients}"
    )


# ============================================================
# STATUS
# ============================================================

st.markdown("---")

st.subheader(
    "📌 Status"
)


if status.upper() == "HIGHLY ADEQUATE":

    st.success(
        f"🟢 {status}"
    )

elif status.upper() == "ADEQUATE":

    st.success(
        f"🟢 {status}"
    )

elif status.upper() == "PARTIALLY ADEQUATE":

    st.warning(
        f"🟠 {status}"
    )

elif status.upper() == "INADEQUATE":

    st.error(
        f"🔴 {status}"
    )

else:

    st.info(
        status
    )


# ============================================================
# INTERPRETATION
# ============================================================

st.markdown("---")

st.subheader(
    "📊 Interpretation"
)


interpretation_col1, interpretation_col2 = (
    st.columns(2)
)


# ============================================================
# CAPACITY INTERPRETATION
# ============================================================

with interpretation_col1:

    st.write(
        "**Capacity Adequacy**"
    )

    if capacity_adequacy >= 80:

        st.success(
            f"✅ Excellent - "
            f"{capacity_adequacy:.1f}% "
            f"(Enough providers for patient volume)"
        )

    elif capacity_adequacy >= 60:

        st.info(
            f"⚠️ Good - "
            f"{capacity_adequacy:.1f}% "
            f"(Adequate but tight)"
        )

    elif capacity_adequacy >= 40:

        st.warning(
            f"⚠️ Fair - "
            f"{capacity_adequacy:.1f}% "
            f"(Some concerns)"
        )

    else:

        st.error(
            f"❌ Poor - "
            f"{capacity_adequacy:.1f}% "
            f"(Not enough providers)"
        )


# ============================================================
# DISTANCE INTERPRETATION
# ============================================================

with interpretation_col2:

    st.write(
        "**Distance Adequacy**"
    )

    if distance_adequacy >= 80:

        st.success(
            f"✅ Excellent - "
            f"{distance_adequacy:.1f}% "
            f"(Good geographic coverage)"
        )

    elif distance_adequacy >= 60:

        st.info(
            f"⚠️ Good - "
            f"{distance_adequacy:.1f}% "
            f"(Adequate coverage)"
        )

    elif distance_adequacy >= 40:

        st.warning(
            f"⚠️ Fair - "
            f"{distance_adequacy:.1f}% "
            f"(Some gaps)"
        )

    else:

        st.error(
            f"❌ Poor - "
            f"{distance_adequacy:.1f}% "
            f"(Poor coverage)"
        )


# ============================================================
# OVERALL ASSESSMENT
# ============================================================

st.markdown("---")

st.subheader(
    "🎯 Overall Assessment"
)


if total_adequacy >= 80:

    st.success(
        f"✅ **Excellent Network Adequacy: "
        f"{total_adequacy:.1f}%**\n\n"
        "The healthcare provider network is "
        "well-positioned to serve the population."
    )

elif total_adequacy >= 60:

    st.info(
        f"⚠️ **Good Network Adequacy: "
        f"{total_adequacy:.1f}%**\n\n"
        "The healthcare provider network is "
        "adequate but could be improved."
    )

elif total_adequacy >= 40:

    st.warning(
        f"⚠️ **Fair Network Adequacy: "
        f"{total_adequacy:.1f}%**\n\n"
        "There are concerns about network "
        "adequacy that should be addressed."
    )

else:

    st.error(
        f"❌ **Poor Network Adequacy: "
        f"{total_adequacy:.1f}%**\n\n"
        "The healthcare provider network "
        "requires significant improvement."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "ℹ️ About"
    )

    st.markdown(
        """
        **CareNet** analyzes healthcare
        provider network adequacy based
        on three backend-provided metrics:

        - **Capacity Adequacy**
        - **Distance Adequacy**
        - **Total Adequacy**

        ---

        ### Data Flow

        `semantic_table.csv`

        ↓

        `FastAPI Backend`

        ↓

        `Streamlit Frontend`

        ---

        **Frontend calculations:**
        None.

        **Data Source:**
        Backend API
        """
    )

    st.markdown("---")

    st.subheader(
        "🔧 Backend Status"
    )


    # ========================================================
    # HEALTH CHECK
    # ========================================================

    try:

        with urlopen(
            f"{API_BASE_URL}/api/health",
            timeout=3
        ) as response:

            health_data = json.loads(
                response
                .read()
                .decode("utf-8")
            )


        if health_data.get(
            "status"
        ) == "healthy":

            st.success(
                "✅ Backend is online"
            )

            if "semantic_table_rows" in health_data:

                st.caption(
                    "Semantic table rows: "
                    +
                    str(
                        health_data[
                            "semantic_table_rows"
                        ]
                    )
                )

        else:

            st.warning(
                "⚠️ Backend is degraded"
            )


    except Exception as error:

        st.error(
            "❌ Backend is offline"
        )

        st.code(
            str(error)
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style='text-align: center;
                color: gray;
                font-size: 12px;'>
        CareNet Network Adequacy Analysis |
        Powered by Streamlit & FastAPI |
        Data served from semantic_table.csv
    </div>
    """,
    unsafe_allow_html=True
)


