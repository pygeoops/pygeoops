from benchmark import benchmarker


def main():
    # Only run specific benchmark function(s)
    benchmarker.run_benchmarks(
        modules_to_run=["benchmarks_alternatives"],
        functions_to_run=[
            "collection_extract2",
            # "simplify_lang",
            # "simplify_lang_plus",
            # "simplify_rdp",
            # "simplify_rdp_keep_points_on",
        ],
    )


if __name__ == "__main__":
    main()
