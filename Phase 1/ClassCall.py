from Building import UsageProcessor
from Alert_Generator import NetworkAlertGenerator


def main():

    # -----------------------------------------------------
    # Input file
    # -----------------------------------------------------

    input_file = (
        "../Dataset/sms-call-internet-mi-2013-11-03.csv"
    )

    # -----------------------------------------------------
    # NP2
    # -----------------------------------------------------

    processor = UsageProcessor(
        file_path=input_file
    )

    hourly_grid_summary = processor.run()
    print("\nProcessing completed successfully.")
    
    print("\nKPIs:")
    
    for key, value in processor.kpis.items():
        print(
                f"{key}: {value}"
            )

    # -----------------------------------------------------
    # NP3
    # -----------------------------------------------------

    alert_generator = NetworkAlertGenerator(
        hourly_grid_summary=hourly_grid_summary,

        activity_floor=None,

        high_threshold=1.50,

        spike_threshold=1.50,

        drop_threshold=0.50
    )

    alerts = alert_generator.run()

    # -----------------------------------------------------
    # Export alerts
    # -----------------------------------------------------

    alert_generator.export_alerts(
        output_dir="outputs"
    )

    # -----------------------------------------------------
    # Print operational summary
    # -----------------------------------------------------

    summary = (
        alert_generator
        .generate_summary()
    )

    print("\nNP3 completed successfully.")

    print(
        "\nTotal grid-hours:",
        summary["total_grid_hours"]
    )

    print(
        "Total alerts:",
        summary["total_alerts"]
    )

    print(
        "Alert proportion:",
        f"{summary['alert_proportion']:.2%}"
    )

    print(
        "\nAlerts by type:"
    )

    for alert_type, count in (
        summary["alerts_by_type"].items()
    ):

        print(
            f"{alert_type}: {count}"
        )

    print(
        "\nTop 10 grids by alert count:"
    )

    for grid_id, count in (
        summary["top_10_grids"].items()
    ):

        print(
            f"Grid {grid_id}: {count}"
        )


if __name__ == "__main__":

    main()