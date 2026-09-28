import re
from typing import Dict, Any, Tuple, List, Optional
from app.schemas.ocr import DutySlipExtractedFields, ExtractedField, CalculatedValidationSummary


def _extract_number(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace("₹", "").replace(",", "")
    if "=" in val_str:
        val_str = val_str.split("=")[-1].strip()
    
    # Check for mixed fraction like "1 1/2" or "2 1/4"
    mixed_frac_match = re.search(r"(\d+)\s+(\d+)/(\d+)", val_str)
    if mixed_frac_match:
        whole = float(mixed_frac_match.group(1))
        num = float(mixed_frac_match.group(2))
        den = float(mixed_frac_match.group(3))
        if den != 0:
            return round(whole + (num / den), 2)
            
    # Check for simple fraction like "1/2"
    frac_match = re.search(r"^(\d+)/(\d+)$", val_str)
    if frac_match:
        num = float(frac_match.group(1))
        den = float(frac_match.group(2))
        if den != 0:
            return round(num / den, 2)

    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _parse_time_to_hours(val: Any) -> Optional[float]:
    if not val:
        return None
    val_str = str(val).strip().upper()
    match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", val_str)
    if not match:
        return None
    hh = int(match.group(1))
    mm = int(match.group(2))
    meridiem = match.group(3)
    if meridiem == "PM" and hh < 12:
        hh += 12
    elif meridiem == "AM" and hh == 12:
        hh = 0
    return round(hh + mm / 60.0, 2)


def normalize_and_validate_extraction(
    raw_fields: Dict[str, Any],
    stored_duty_slip_no: str,
    has_back_scan: bool = True
) -> Tuple[DutySlipExtractedFields, CalculatedValidationSummary, float, bool, List[str]]:
    """
    Validate, normalize, and evaluate confidence/review flags for extracted fields.
    Performs package excess validation (8hr / 80km package) without overwriting document values.
    Returns (DutySlipExtractedFields, CalculatedValidationSummary, overall_confidence, needs_review, review_reasons).
    """
    fields_dict: Dict[str, ExtractedField] = {}
    review_reasons: List[str] = []
    confidence_scores: List[float] = []
    overall_needs_review = False

    expected_front_fields = [
        "duty_slip_no",
        "date",
        "driver_name",
        "vehicle_number",
        "meter_start",
        "meter_return",
        "total_km",
        "starting_time",
        "closing_time",
        "extra_km",
        "extra_hours",
        "reporting_place",
        "tour_location",
        "party_name",
        "customer_name",
        "remarks",
    ]

    expected_back_fields = [
        "base_package",
        "extra_km_charge",
        "extra_hour_charge",
        "bata",
        "toll",
        "total_amount",
    ]

    all_expected_fields = expected_front_fields + expected_back_fields

    # Sync party_name and customer_name if only one is provided
    if "party_name" in raw_fields and "customer_name" not in raw_fields:
        raw_fields["customer_name"] = raw_fields["party_name"]
    elif "customer_name" in raw_fields and "party_name" not in raw_fields:
        raw_fields["party_name"] = raw_fields["customer_name"]

    for fname in all_expected_fields:
        raw_val = raw_fields.get(fname)
        is_back_field = fname in expected_back_fields

        if isinstance(raw_val, dict):
            val = raw_val.get("value")
            conf = float(raw_val.get("confidence", 0.0))
            needs_rev = bool(raw_val.get("needs_review", False))
            rev_reason = raw_val.get("review_reason")
            raw_t = raw_val.get("raw_text")
            src_side = raw_val.get("source_side") or ("back" if is_back_field else "front")
            orig_val = raw_val.get("original_value", val)
            is_edited = bool(raw_val.get("edited", False))
            ed_at = raw_val.get("edited_at")
            ed_by = raw_val.get("edited_by")
        else:
            val = raw_val
            conf = 0.90 if raw_val is not None else 0.0
            needs_rev = val is None
            rev_reason = "missing_field" if val is None else None
            raw_t = str(raw_val) if raw_val is not None else None
            src_side = "back" if is_back_field else "front"
            orig_val = val
            is_edited = False
            ed_at = None
            ed_by = None

        # If this is a back field and there is NO back scan, it is normal to have null value
        if is_back_field and not has_back_scan:
            needs_rev = False
            rev_reason = None
            conf = 1.0

        # If manually edited by human reviewer and value is provided, clear unreadable/low confidence flags
        if is_edited and val is not None:
            needs_rev = False
            rev_reason = None

        # Check low confidence (only for unedited fields)
        if not is_edited and conf < 0.80 and val is not None:
            needs_rev = True
            if not rev_reason:
                rev_reason = "low_confidence"
            if "low_confidence" not in review_reasons:
                review_reasons.append("low_confidence")

        # Check unreadable / missing on required front fields
        if val is None:
            if fname in ["party_name", "customer_name", "remarks"]:
                needs_rev = False
                rev_reason = None
            elif fname == "duty_slip_no":
                needs_rev = True
                if not rev_reason:
                    rev_reason = "unreadable_field"
                if "unreadable_field" not in review_reasons:
                    review_reasons.append("unreadable_field")
            elif not is_back_field or has_back_scan:
                needs_rev = True
                if not rev_reason:
                    rev_reason = "unreadable_field"
                if "unreadable_field" not in review_reasons:
                    review_reasons.append("unreadable_field")

        if needs_rev:
            overall_needs_review = True

        confidence_scores.append(conf)

        fields_dict[fname] = ExtractedField(
            value=val,
            confidence=round(conf, 2),
            needs_review=needs_rev,
            review_reason=rev_reason,
            raw_text=raw_t,
            source_side=src_side,
            original_value=orig_val,
            edited=is_edited,
            edited_at=ed_at,
            edited_by=ed_by
        )

    # 1. Compare Duty Slip Number (only if printed on physical document)
    extracted_ds_no = fields_dict["duty_slip_no"].value
    if extracted_ds_no is not None and str(extracted_ds_no).strip():
        clean_ext_no = str(extracted_ds_no).strip().lstrip("#")
        clean_stored_no = str(stored_duty_slip_no).strip()
        if clean_ext_no != clean_stored_no:
            fields_dict["duty_slip_no"].needs_review = True
            fields_dict["duty_slip_no"].review_reason = f"duty_slip_number_mismatch: OCR detected '{clean_ext_no}', expected '{clean_stored_no}'"
            overall_needs_review = True
            if "duty_slip_number_mismatch" not in review_reasons:
                review_reasons.append("duty_slip_number_mismatch")

    # 2. KM Consistency Validations (meter_return - meter_start vs total_km)
    m_start = _extract_number(fields_dict["meter_start"].value)
    m_ret = _extract_number(fields_dict["meter_return"].value)
    tot_km = _extract_number(fields_dict["total_km"].value)
    calc_total_km = None
    is_km_consistent = True

    if m_start is not None and m_ret is not None:
        calc_total_km = round(m_ret - m_start, 2)
        if m_ret < m_start:
            fields_dict["meter_return"].needs_review = True
            fields_dict["meter_return"].review_reason = "validation_failure: meter_return is less than meter_start"
            overall_needs_review = True
            is_km_consistent = False
            if "validation_failure" not in review_reasons:
                review_reasons.append("validation_failure")
        elif tot_km is not None:
            if abs(calc_total_km - tot_km) > 0.01:
                fields_dict["total_km"].needs_review = True
                fields_dict["total_km"].review_reason = f"validation_failure: total_km ({tot_km}) does not match meter_return - meter_start ({calc_total_km})"
                overall_needs_review = True
                is_km_consistent = False
                if "validation_failure" not in review_reasons:
                    review_reasons.append("validation_failure")

    # 3. Time Elapsed & Extra Hours Validation (Package 8 Hours)
    start_hrs = _parse_time_to_hours(fields_dict["starting_time"].value)
    close_hrs = _parse_time_to_hours(fields_dict["closing_time"].value)
    calc_total_hrs = None
    calc_extra_hrs = None
    is_time_consistent = True

    if start_hrs is not None and close_hrs is not None:
        calc_total_hrs = round(close_hrs - start_hrs if close_hrs >= start_hrs else (close_hrs + 24.0) - start_hrs, 2)
        calc_extra_hrs = max(0.0, round(calc_total_hrs - 8.0, 2))
        doc_extra_hrs = _extract_number(fields_dict["extra_hours"].value)
        if doc_extra_hrs is not None:
            if abs(doc_extra_hrs - calc_extra_hrs) > 0.1:
                fields_dict["extra_hours"].needs_review = True
                fields_dict["extra_hours"].review_reason = f"validation_failure: extra_hours ({doc_extra_hrs}) does not match calculated extra hours ({calc_extra_hrs}) from {fields_dict['starting_time'].value} to {fields_dict['closing_time'].value}"
                overall_needs_review = True
                is_time_consistent = False
                if "validation_failure" not in review_reasons:
                    review_reasons.append("validation_failure")

    # 4. Extra KM Validation (Package 80 KM)
    calc_extra_km = None
    active_tot_km = tot_km if tot_km is not None else calc_total_km
    if active_tot_km is not None:
        calc_extra_km = max(0.0, round(active_tot_km - 80.0, 2))
        doc_extra_km = _extract_number(fields_dict["extra_km"].value)
        if doc_extra_km is not None:
            if abs(doc_extra_km - calc_extra_km) > 0.1:
                fields_dict["extra_km"].needs_review = True
                fields_dict["extra_km"].review_reason = f"validation_failure: extra_km ({doc_extra_km}) does not match calculated extra km ({calc_extra_km}) for {active_tot_km} total KM"
                overall_needs_review = True
                is_km_consistent = False
                if "validation_failure" not in review_reasons:
                    review_reasons.append("validation_failure")

    # 5. Back Calculation Math Validation (if back scan exists)
    calc_extra_km_amt = round(calc_extra_km * 15.0, 2) if calc_extra_km is not None else None
    calc_extra_hr_amt = round(calc_extra_hrs * 150.0, 2) if calc_extra_hrs is not None else None
    calc_total_amt = None
    is_math_consistent = True

    if has_back_scan:
        base_amt = _extract_number(fields_dict["base_package"].value)
        extra_km_amt = _extract_number(fields_dict["extra_km_charge"].value)
        extra_hr_amt = _extract_number(fields_dict["extra_hour_charge"].value)
        bata_amt = _extract_number(fields_dict["bata"].value)
        toll_amt = _extract_number(fields_dict["toll"].value)
        total_amt = _extract_number(fields_dict["total_amount"].value)

        # Check sum if line items are present
        items = [base_amt, extra_km_amt, extra_hr_amt, bata_amt, toll_amt]
        if all(x is not None for x in items):
            calc_total_amt = round(sum(items), 2)
            if total_amt is not None and abs(calc_total_amt - total_amt) > 0.01:
                fields_dict["total_amount"].needs_review = True
                fields_dict["total_amount"].review_reason = f"validation_failure: total amount ({total_amt}) does not match sum of charges ({calc_total_amt})"
                overall_needs_review = True
                is_math_consistent = False
                if "validation_failure" not in review_reasons:
                    review_reasons.append("validation_failure")

    # Overall Confidence Calculation
    overall_conf = round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0.0

    validation_summary = CalculatedValidationSummary(
        calculated_total_km=calc_total_km if calc_total_km is not None else tot_km,
        calculated_total_hours=calc_total_hrs,
        calculated_extra_km=calc_extra_km,
        calculated_extra_hours=calc_extra_hrs,
        calculated_extra_km_amount=calc_extra_km_amt,
        calculated_extra_hour_amount=calc_extra_hr_amt,
        calculated_total_amount=calc_total_amt,
        is_km_consistent=is_km_consistent,
        is_time_consistent=is_time_consistent,
        is_math_consistent=is_math_consistent
    )

    return DutySlipExtractedFields(**fields_dict), validation_summary, overall_conf, overall_needs_review, review_reasons


