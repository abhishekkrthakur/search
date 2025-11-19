from vespa.package import (
    ApplicationPackage,
    Document,
    Field,
    FieldSet,
    Function,
    RankProfile,
    Schema,
)
from vespa.deployment import VespaDocker
from vespa.io import VespaResponse
from datasets import load_dataset
from tqdm import tqdm

package = ApplicationPackage(
    name="simplesearch",
    schema=[
        Schema(
            name="doc",
            document=Document(
                fields=[
                    Field(
                        name="id",
                        type="string",
                        indexing=["summary"],
                    ),
                    Field(
                        name="text",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="url",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                ]
            ),
            fieldsets=[
                FieldSet(name="default", fields=["text", "url"]),
            ],
            rank_profiles=[
                # 1) BM25 only on text
                RankProfile(
                    name="bm25_text_only",
                    functions=[
                        Function(
                            name="bm25text",
                            expression="bm25(text)",
                        ),
                    ],
                    first_phase="bm25text",
                ),
                # 2) BM25 only on url
                RankProfile(
                    name="bm25_url_only",
                    functions=[
                        Function(
                            name="bm25url",
                            expression="bm25(url)",
                        ),
                    ],
                    first_phase="bm25url",
                ),
                # 3) Original combined BM25 (defaults for k and b)
                RankProfile(
                    name="bm25",
                    functions=[
                        Function(
                            name="bm25texturl",
                            expression="bm25(text) + 0.1 * bm25(url)",
                        ),
                    ],
                    first_phase="bm25texturl",
                ),
                # --- 4) Combined BM25 with different k and b ---
                RankProfile(
                    name="bm25_comb_tuned",
                    functions=[
                        Function(
                            name="bm25texturl_tuned",
                            expression="bm25(text) + 0.1 * bm25(url)",
                        ),
                    ],
                    first_phase="bm25texturl_tuned",
                    rank_properties=[
                        ("bm25(text).k1", "1.8"),
                        ("bm25(text).b", "0.40"),
                        ("bm25(url).k1", "0.9"),
                        ("bm25(url).b", "0.30"),
                    ],
                ),
            ],
        ),
    ],
)

vespa_docker = VespaDocker()
app = vespa_docker.deploy(application_package=package)
package.to_files(root="./vespa_app")
