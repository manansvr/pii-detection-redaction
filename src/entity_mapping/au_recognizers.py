# src/entity_mapping/au_recognizers.py

from __future__ import annotations

from presidio_analyzer import PatternRecognizer, Pattern


class AbnRecognizer(PatternRecognizer):
    _abn_weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    def __init__(self):
        patterns = [
            Pattern(
                name="abn_spaced",
                regex=r"\b(?:\d[ ]?){11}\b",
                score=0.5,
            ),
            Pattern(
                name="abn_grouped",
                regex=r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b",
                score=0.6,
            ),
            Pattern(
                name="abn_plain",
                regex=r"\b\d{11}\b",
                score=0.45,
            ),
        ]

        super().__init__(
            supported_entity="AU_ABN",
            patterns=patterns,
            context=["abn", "australian business number", "business number", "abn number"],
        )

    @staticmethod
    def is_valid_abn(text: str) -> bool:
        digits = [int(c) for c in text if c.isdigit()]
        if len(digits) != 11:
            return False

        digits[0] -= 1
        total = sum(d * w for d, w in zip(digits, AbnRecognizer._abn_weights))

        return total % 89 == 0

    def validate_result(self, pattern_text: str) -> bool:
        digits_only = "".join(c for c in pattern_text if c.isdigit())
        return self.is_valid_abn(digits_only)


class AcnRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="acn_spaced",
                regex=r"\b\d{3}\s?\d{3}\s?\d{3}\b",
                score=0.5,
            ),
            Pattern(
                name="acn_plain",
                regex=r"\b\d{9}\b",
                score=0.4,
            ),
        ]

        super().__init__(
            supported_entity="AU_ACN",
            patterns=patterns,
            context=["acn", "australian company number", "company number", "acn number"],
        )


class TfnRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="tfn_spaced",
                regex=r"\b\d{3}\s?\d{3}\s?\d{3}\b",
                score=0.5,
            ),
            Pattern(
                name="tfn_dashed",
                regex=r"\b\d{3}-\d{3}-\d{3}\b",
                score=0.6,
            ),
            Pattern(
                name="tfn_plain",
                regex=r"\b\d{9}\b",
                score=0.4,
            ),
        ]

        super().__init__(
            supported_entity="AU_TFN",
            patterns=patterns,
            context=["tfn", "tax file number", "tax file no", "tax file"],
        )


class MedicareNumberRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="medicare_spaced",
                regex=r"\b\d{4}\s?\d{5}\s?\d{1}\b",
                score=0.6,
            ),
            Pattern(
                name="medicare_plain",
                regex=r"\b\d{10}\s?\d{1}\b",
                score=0.55,
            ),
        ]

        super().__init__(
            supported_entity="AU_MEDICARE",
            patterns=patterns,
            context=["medicare", "medicare number", "medicare card", "medicare no"],
        )


class CentrelinkCrnRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="crn_10_digit",
                regex=r"\b\d{10}\b",
                score=0.4,
            ),
            Pattern(
                name="crn_9_digit",
                regex=r"\b\d{9}\b",
                score=0.35,
            ),
            Pattern(
                name="crn_spaced",
                regex=r"\b\d{3}\s?\d{3}\s?\d{3,4}\b",
                score=0.45,
            ),
        ]

        super().__init__(
            supported_entity="AU_CENTRELINK_CRN",
            patterns=patterns,
            context=[
                "crn",
                "customer reference number",
                "centrelink",
                "centrelink number",
                "reference number",
            ],
        )


class BsbRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="bsb_dashed",
                regex=r"\b\d{3}-\d{3}\b",
                score=0.7,
            ),
            Pattern(
                name="bsb_spaced",
                regex=r"\b\d{3}\s\d{3}\b",
                score=0.65,
            ),
            Pattern(
                name="bsb_plain",
                regex=r"\b\d{6}\b",
                score=0.4,
            ),
        ]

        super().__init__(
            supported_entity="AU_BSB",
            patterns=patterns,
            context=["bsb", "bank state branch", "branch code", "bsb code"],
        )


class AuDriverLicenseRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            # NSW: 8 digits
            Pattern(
                name="driver_license_nsw",
                regex=r"\b\d{8}\b",
                score=0.4,
            ),
            # VIC: 10 digits
            Pattern(
                name="driver_license_vic",
                regex=r"\b\d{10}\b",
                score=0.4,
            ),
            # QLD: 8-9 digits
            Pattern(
                name="driver_license_qld",
                regex=r"\b\d{8,9}\b",
                score=0.35,
            ),
            # SA: 6 digits + 1 letter
            Pattern(
                name="driver_license_sa_alpha",
                regex=r"\b\d{6}[A-Z]\b",
                score=0.5,
            ),
            # WA: 7 digits
            Pattern(
                name="driver_license_wa",
                regex=r"\b\d{7}\b",
                score=0.4,
            ),
            Pattern(
                name="driver_license_general",
                regex=r"\b[A-Z0-9]{6,10}\b",
                score=0.3,
            ),
        ]

        super().__init__(
            supported_entity="AU_DRIVER_LICENSE",
            patterns=patterns,
            context=[
                "driver license",
                "driver licence",
                "drivers license",
                "driving licence",
                "dl number",
                "license number",
                "licence number",
                "dl no",
            ],
        )


class AuPassportRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="passport_new_format",
                regex=r"\b[A-Z]{1,2}\d{7}\b",
                score=0.6,
            ),
            Pattern(
                name="passport_spaced",
                regex=r"\b[A-Z]{1,2}\s?\d{7}\b",
                score=0.55,
            ),
        ]

        super().__init__(
            supported_entity="AU_PASSPORT",
            patterns=patterns,
            context=[
                "passport",
                "passport number",
                "passport no",
                "australian passport",
                "travel document",
            ],
        )


class AuPhoneRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="phone_mobile_intl",
                regex=r"\+61\s?4\d{2}\s?\d{3}\s?\d{3}",
                score=0.7,
            ),
            Pattern(
                name="phone_mobile_domestic",
                regex=r"\b04\d{2}\s?\d{3}\s?\d{3}\b",
                score=0.65,
            ),
            Pattern(
                name="phone_landline_brackets",
                regex=r"\(0[2-8]\)\s?\d{4}\s?\d{4}",
                score=0.6,
            ),
            Pattern(
                name="phone_landline_intl",
                regex=r"\+61\s?[2-8]\s?\d{4}\s?\d{4}",
                score=0.7,
            ),
            Pattern(
                name="phone_tollfree",
                regex=r"\b1[38]00\s?\d{3}\s?\d{3}\b",
                score=0.6,
            ),
        ]

        super().__init__(
            supported_entity="AU_PHONE_NUMBER",
            patterns=patterns,
            context=[
                "phone",
                "telephone",
                "mobile",
                "contact",
                "call",
                "tel",
                "ph",
            ],
        )


def build_au_recognizers() -> list[PatternRecognizer]:
    recognizers: list[PatternRecognizer] = []

    recognizers.append(TfnRecognizer())
    recognizers.append(MedicareNumberRecognizer())
    recognizers.append(CentrelinkCrnRecognizer())
    recognizers.append(AuDriverLicenseRecognizer())
    recognizers.append(AuPassportRecognizer())

    recognizers.append(AbnRecognizer())
    recognizers.append(AcnRecognizer())
    recognizers.append(BsbRecognizer())

    recognizers.append(AuPhoneRecognizer())

    bank_patterns = [
        Pattern(
            name="bank_account_typical",
            regex=r"\b\d{6}[- ]?\d{6,10}\b",
            score=0.45,
        ),
        Pattern(
            name="bank_account_long",
            regex=r"\b\d{8,12}\b",
            score=0.3,
        ),
        Pattern(
            name="bank_account_short",
            regex=r"\b\d{6,7}\b",
            score=0.25,
        ),
    ]

    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_BANK_ACCOUNT",
            patterns=bank_patterns,
            context=[
                "bank account",
                "account number",
                "acct no",
                "account no",
                "acc no",
                "bsb",
                "account",
            ],
        )
    )

    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_STATE",
            deny_list=[
                "NSW",
                "VIC",
                "QLD",
                "SA",
                "WA",
                "TAS",
                "ACT",
                "NT",
                "New South Wales",
                "Victoria",
                "Queensland",
                "South Australia",
                "Western Australia",
                "Tasmania",
                "Australian Capital Territory",
                "Northern Territory",
            ],
        )
    )

    postcode_patterns = [
        Pattern(
            name="postcode_4digit",
            regex=r"\b\d{4}\b",
            score=0.35,
        )
    ]

    recognizers.append(
        PatternRecognizer(
            supported_entity="AU_POSTCODE",
            patterns=postcode_patterns,
            context=[
                "postcode",
                "postal code",
                "post code",
                "delivery address",
                "suburb",
                "address",
                "postcode:",
                "post:",
            ],
        )
    )

    return recognizers