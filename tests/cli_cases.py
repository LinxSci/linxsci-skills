"""Independent CLI scenarios for route tests and installed-package smoke checks.

Bodies are synthetic transport fixtures, not production API schemas.
"""


def shortcut_cases(ids, body_file, pdf_file):
    body = ["--body", "@" + str(body_file)]
    cases = {
        ("GET", "/meta"): ["meta"],
        ("GET", "/usage"): ["usage"],
        ("GET", "/health/live"): ["health", "live"],
        ("GET", "/health/ready"): ["health", "ready"],
        ("POST", "/papers/search"): ["search", "release coverage"] + body,
        ("POST", "/search/openalex"): ["search-openalex", "release coverage"] + body,
        ("POST", "/search/semantic-scholar"): ["search-semantic-scholar", "release coverage"] + body,
        ("POST", "/search/google-scholar"): ["search-google-scholar", "release coverage"] + body,
        ("POST", "/papers/resolve"): ["resolve"] + body,
        ("POST", "/papers:batchGet"): ["batch-get"] + body,
        ("POST", "/recommendations"): ["recommend"] + body,
        ("GET", "/recommendations/mobile-cards"): ["mobile-cards"],
        ("POST", "/entities:resolve"): ["resolve-entities"] + body,
        ("POST", "/pdf/parse"): ["parse-pdf"] + body,
        ("POST", "/pdf/parse/upload"): ["upload", str(pdf_file)],
        ("GET", "/pdf/parse/{task_id}"): ["task", ids["task_id"]],
        ("GET", "/pdf/parse/{task_id}/result"): ["task", ids["task_id"], "--result"],
        ("GET", "/papers/{paper_id}"): ["paper", ids["paper_id"]],
    }
    for resource in ("content", "toc", "figures", "references", "citations", "related", "graph", "citation"):
        cases[("GET", "/papers/{paper_id}/" + resource)] = ["paper", ids["paper_id"], "--resource", resource]
    for resource, item in (("sections", "section_id"), ("assets", "asset_id")):
        cases[("GET", "/papers/{paper_id}/" + resource + "/{" + item + "}")] = [
            "paper", ids["paper_id"], "--resource", resource, "--item-id", ids[item]]
    for command, collection, item in (("author", "authors", "author_id"),
                                      ("institution", "institutions", "institution_id"),
                                      ("venue", "venues", "venue_id")):
        for suffix in ("", "/papers"):
            cases[("GET", "/" + collection + "/{" + item + "}" + suffix)] = [
                command, ids[item]] + (["--papers"] if suffix else [])
    return cases
