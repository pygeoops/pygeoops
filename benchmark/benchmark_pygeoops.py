"""Main module to run benchmarks."""

from benchmark import benchmarker


def main():
    """Main function to run benchmarks."""
    # Only run specific benchmark function(s)
    benchmarker.run_benchmarks(
        modules_to_run=["benchmarks_pygeoops"],
        functions_to_run=[
            "buffer_by_m_lines",
            # "simplify_lang",
            # "simplify_lang_plus",
            # "simplify_rdp",
            # "simplify_rdp_keep_points_on",
        ],
    )


if __name__ == "__main__":
    main()
