import benchmarker


def main():
    # Only run specific benchmark function(s)
    benchmarker.run_benchmarks(
        modules_to_run=["benchmarks_pygeoops"],
        functions_to_run=[
            "simplify_lang",
            "simplify_lang_plus",
            # "simplify_rdp",
            # "simplify_rdp_keep_points_on",
        ],
    )


if __name__ == "__main__":
    main()
