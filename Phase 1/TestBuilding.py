from Building import UsageProcessor

# ---------------------------------------------------------
# NP2 Validation Test
# ---------------------------------------------------------

def test_np2_validation():
    input_file = (
        "../Dataset/sms-call-internet-mi-2013-11-02.csv"
    )
    processor = UsageProcessor(
        file_path=input_file
    )
    processor.run()
    assert processor.raw_df is not None, \
        "Raw DataFrame was not loaded."
    assert processor.rejected_rows >= 0, \
        "Rejected row count cannot be negative."
    assert processor.nulls_handled >= 0, \
        "Null count cannot be negative."
    duplicate_count = (
        processor.hourly_grid_summary
        .duplicated(
            subset=[
                "grid_id",
                "timestamp"
            ]
        )
        .sum()
    )
    assert duplicate_count == 0, \
        f"Found {duplicate_count} duplicate grid/hour records."
    assert (
        "country_code"
        not in processor.hourly_grid_summary.columns
    ), \
        "country_code should not exist after aggregation."
    assert (
        len(processor.hourly_grid_summary)
        < len(processor.df)
    ), \
        "Aggregation did not reduce the number of rows."
    assert processor.kpis is not None, \
        "KPIs were not calculated."
    print("NP2 validation PASSED")

if __name__ == "__main__":

    test_np2_validation()