import streamlit as st

# Import centralized entity mappings
try:
    from entity_mapping import (
        ALL_AU_ENTITY_TYPES,
        AU_ENTITY_SEVERITY_MAP,
        AU_ENTITY_GROUPS,
        get_entity_severity,
        get_entities_by_group,
    )
    HAS_ENTITY_MAPPING = True
except ImportError:
    HAS_ENTITY_MAPPING = False


def render_entity_mapping_tab():
    """Render the entity mapping information tab."""
    st.subheader("🇦🇺 Australian Entity Mapping")
    st.caption(
        "This module provides centralized entity recognition for Australian-specific PII types."
    )
    st.caption(
        "All recognizers use regex patterns, context keywords, and validation algorithms "
        "to accurately detect and classify sensitive information across different formats."
    )

    if not HAS_ENTITY_MAPPING:
        st.error("⚠️ Entity mapping module not available. Please ensure the entity_mapping module is properly installed.")
        return

    st.markdown("---")
    st.markdown("### 📋")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Entities", len(ALL_AU_ENTITY_TYPES))
    with col2:
        critical_count = len([e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "critical"])
        st.metric("Critical", critical_count, delta_color="inverse")
    with col3:
        high_count = len([e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "high"])
        st.metric("High", high_count, delta_color="inverse")
    with col4:
        medium_count = len([e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "medium"])
        st.metric("Medium", medium_count)

    st.markdown("---")
    st.markdown("### 🎯 Entity Classification by Severity")

    severity_tab1, severity_tab2, severity_tab3, severity_tab4 = st.tabs([
        "🔴 Critical",
        "🟠 High",
        "🟡 Medium",
        "🔵 Low"
    ])

    with severity_tab1:
        critical_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "critical"]
        if critical_entities:
            st.markdown("""
            **Critical entities** are highly sensitive government-issued identifiers that require 
            the highest level of protection. Exposure of these can lead to identity theft or fraud.
            """)
            for entity in critical_entities:
                display_entity_details(entity)
        else:
            st.info("No Critical Entities Defined.")

    with severity_tab2:
        high_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "high"]
        if high_entities:
            st.markdown("""
            **High severity entities** include financial identifiers and business numbers that 
            could be used for financial fraud or unauthorized transactions.
            """)
            for entity in high_entities:
                display_entity_details(entity)
        else:
            st.info("No High Severity Entities Defined.")

    with severity_tab3:
        medium_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "medium"]
        if medium_entities:
            st.markdown("""
            **Medium severity entities** are personal contact information that should be protected 
            but may have lower risk compared to government or financial identifiers.
            """)
            for entity in medium_entities:
                display_entity_details(entity)
        else:
            st.info("No Medium Severity Entities Defined.")
    
    with severity_tab4:
        low_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "low"]
        if low_entities:
            st.markdown("""
            **Low severity entities** are geographic or general identifiers. While not highly 
            sensitive alone, they can contribute to re-identification when combined with other data.
            """)
            for entity in low_entities:
                display_entity_details(entity)
        else:
            st.info("No Low Severity Entities Defined.")
    
    st.markdown("---")
    st.markdown("### 📦 Entity Groups")
    st.markdown("Entities are organized into functional groups for easier management and filtering.")
    
    try:
        financial_entities = get_entities_by_group("financial")
        government_entities = get_entities_by_group("government_id")
        personal_entities = get_entities_by_group("personal")
        geographic_entities = get_entities_by_group("geographic")
        all_au_entities = get_entities_by_group("all_au_specific")
        
        group_col1, group_col2 = st.columns(2)
        
        with group_col1:
            with st.expander("💰 Financial Entities", expanded=False):
                if financial_entities:
                    for entity in financial_entities:
                        st.markdown(f"- `{entity}`")
                else:
                    st.info("No Financial Entities Defined.")
            
            with st.expander("🏛️ Government IDs", expanded=False):
                if government_entities:
                    for entity in government_entities:
                        st.markdown(f"- `{entity}`")
                else:
                    st.info("No Government Entities Defined.")
        
        with group_col2:
            with st.expander("👤 Personal Information", expanded=False):
                if personal_entities:
                    for entity in personal_entities:
                        st.markdown(f"- `{entity}`")
                else:
                    st.info("No Personal Entities Defined.")
            
            with st.expander("📍 Geographic Data", expanded=False):
                if geographic_entities:
                    for entity in geographic_entities:
                        st.markdown(f"- `{entity}`")
                else:
                    st.info("No Geographic Entities Defined.")
        
        with st.expander("🇦🇺 All Australian-Specific Entities", expanded=False):
            if all_au_entities:
                st.markdown(f"**Total: {len(all_au_entities)} entities**")
                for entity in all_au_entities:
                    st.markdown(f"- `{entity}`")
            else:
                st.info("No Australian-Specific Entities Defined.")
    except Exception as e:
        st.warning(f"Could not load entity groups: {e}")

    st.markdown("---")
    st.markdown("### ⚙️ Technical Implementation")

    with st.expander("🛠️ Integration Points"):
        st.markdown("""
        The entity mapping module is integrated across all detection modules:
        
        - **Text Detector** (`text_detector`): Uses recognizers for plain text analysis
        - **PDF Redactor** (`pdf_redactor`): Applies recognizers to PDF content
        - **CSV Redactor** (`csv_redactor`): Detects PII in structured CSV data
        - **Image Redactor** (`image_redactor`): Recognizes text entities in OCR'd images
        - **Common Module** (`common`): Builds the centralized analyzer instance
        
        All modules pull from the same entity definitions, ensuring consistency.
        """)
    
    with st.expander("📚 Entity Descriptions"):
        st.markdown("""
        #### Government & Identity
        - **AU_ABN**: Australian Business Number (11 Digits With Validation)
        - **AU_ACN**: Australian Company Number (9 Digits)
        - **AU_TFN**: Tax File Number (9 Digits, Highly Sensitive)
        - **AU_MEDICARE**: Medicare Number (10+1 Digit Format)
        - **AU_CENTRELINK_CRN**: Centrelink Customer Reference Number
        - **AU_DRIVER_LICENSE**: State-Specific Driver License Formats
        - **AU_PASSPORT**: Australian Passport Numbers (L1234567 Format)
        
        #### Financial
        - **AU_BSB**: Bank State Branch Codes (6 Digits, XXX-XXX Format)
        - **AU_BANK_ACCOUNT**: Australian Bank Account Numbers (Various Formats)
        
        #### Contact & Personal
        - **AU_PHONE_NUMBER**: Mobile, Landline, And Toll-Free Numbers
        - **EMAIL_ADDRESS**: Email Addresses (Presidio Built-In)
        - **PERSON**: Person Names (Presidio Built-In)
        
        #### Geographic
        - **AU_STATE**: Australian States And Territories (Abbreviations And Full Names)
        - **AU_POSTCODE**: 4-Digit Australian Postcodes
        """)


def display_entity_details(entity_type: str):
    severity = get_entity_severity(entity_type)

    entity_info = {
        "AU_ABN": {
            "name": "Australian Business Number",
            "description": "11-Digit Identifier With Checksum Validation (Modulo 89)",
            "examples": ["51 824 753 556", "51824753556"],
            "formats": ["XX XXX XXX XXX", "XXXXXXXXXXX"]
        },
        "AU_ACN": {
            "name": "Australian Company Number",
            "description": "9-Digit Identifier For ASIC-Registered Companies",
            "examples": ["123 456 789", "123456789"],
            "formats": ["XXX XXX XXX", "XXXXXXXXX"]
        },
        "AU_TFN": {
            "name": "Tax File Number",
            "description": "9-Digit Tax Identifier Issued By ATO",
            "examples": ["123 456 782", "123-456-782"],
            "formats": ["XXX XXX XXX", "XXX-XXX-XXX"]
        },
        "AU_MEDICARE": {
            "name": "Medicare Number",
            "description": "10 Digits + 1 Position Digit For Medicare Card",
            "examples": ["2123 45670 1", "212345670 1"],
            "formats": ["XXXX XXXXX X"]
        },
        "AU_CENTRELINK_CRN": {
            "name": "Centrelink Customer Reference Number",
            "description": "9 Or 10-Digit Centrelink Customer Identifier",
            "examples": ["123 456 789", "1234567890"],
            "formats": ["XXX XXX XXX", "XXXXXXXXXX"]
        },
        "AU_BSB": {
            "name": "Bank State Branch",
            "description": "6-Digit Bank Branch Identifier",
            "examples": ["062-000", "062000"],
            "formats": ["XXX-XXX", "XXXXXX"]
        },
        "AU_DRIVER_LICENSE": {
            "name": "Driver License Number",
            "description": "State-Specific Formats (NSW: 8 Digits, VIC: 10 Digits, Etc.)",
            "examples": ["12345678 (NSW)", "1234567890 (VIC)", "123456A (SA)"],
            "formats": ["Varies By State"]
        },
        "AU_PASSPORT": {
            "name": "Australian Passport",
            "description": "1-2 Letters + 7 Digits",
            "examples": ["N1234567", "PA1234567"],
            "formats": ["L1234567", "LL1234567"]
        },
        "AU_PHONE_NUMBER": {
            "name": "Australian Phone Number",
            "description": "Mobile, Landline, And Toll-Free Numbers",
            "examples": ["0412 345 678", "+61 2 9876 5432", "1300 123 456"],
            "formats": ["04XX XXX XXX", "+61 X XXXX XXXX", "1300/1800"]
        },
        "AU_BANK_ACCOUNT": {
            "name": "Bank Account Number",
            "description": "Australian Bank Account Numbers (6-12 Digits)",
            "examples": ["123456 789012", "12345678"],
            "formats": ["XXXXXX-XXXXXX", "XXXXXXXX"]
        },
        "AU_STATE": {
            "name": "Australian State/Territory",
            "description": "State And Territory Names Or Abbreviations",
            "examples": ["NSW", "Victoria", "QLD"],
            "formats": ["Abbreviation Or Full Name"]
        },
        "AU_POSTCODE": {
            "name": "Australian Post-Code",
            "description": "4-Digit Postal Code",
            "examples": ["2000", "3000", "4000"],
            "formats": ["XXXX"]
        },
    }
    
    info = entity_info.get(entity_type)
    
    if info:
        with st.container():
            st.markdown(f"#### `{entity_type}`")
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{info['name']}**")
                st.caption(info['description'])
            with cols[1]:
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵"
                }
                st.markdown(f"{severity_emoji.get(severity, '')} `{severity.upper()}`")
            
            with st.expander("View Examples & Formats"):
                st.markdown("**Example Values:**")
                for example in info['examples']:
                    st.code(example, language=None)
                
                st.markdown("**Accepted Formats:**")
                if isinstance(info['formats'], list):
                    for fmt in info['formats']:
                        st.markdown(f"- `{fmt}`")
                else:
                    st.markdown(f"- `{info['formats']}`")
            
            st.markdown("---")
    else:
        st.markdown(f"#### `{entity_type}`")
        st.caption(f"Severity: {severity.upper()}")
        st.markdown("---")
