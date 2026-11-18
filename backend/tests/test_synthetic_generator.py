import pytest
from backend.app.synthetic.generator import SyntheticConfig, SyntheticDataGenerator


def test_synthetic_reproducibility():
    config1 = SyntheticConfig(seed=42, num_students=10, num_faculty=8, num_publications=15)
    config2 = SyntheticConfig(seed=42, num_students=10, num_faculty=8, num_publications=15)

    gen1 = SyntheticDataGenerator(config1)
    gen2 = SyntheticDataGenerator(config2)

    data1 = gen1.generate()
    data2 = gen2.generate()

    # Exact equality across repeated runs with identical seed
    assert len(data1.students) == len(data2.students) == 10
    assert len(data1.faculty) == len(data2.faculty) == 8
    assert len(data1.publications) == len(data2.publications) == 15

    for s1, s2 in zip(data1.students, data2.students):
        assert s1.email == s2.email
        assert s1.statement_of_purpose == s2.statement_of_purpose

    for p1, p2 in zip(data1.publications, data2.publications):
        assert p1.title == p2.title
        assert p1.doi == p2.doi


def test_synthetic_seed_variation():
    config1 = SyntheticConfig(seed=42, num_students=5, num_faculty=5, num_publications=5)
    config2 = SyntheticConfig(seed=999, num_students=5, num_faculty=5, num_publications=5)

    data1 = SyntheticDataGenerator(config1).generate()
    data2 = SyntheticDataGenerator(config2).generate()

    # Different seeds must produce different students and publications
    assert data1.students[0].email != data2.students[0].email
    assert [p.author_names for p in data1.publications] != [p.author_names for p in data2.publications]
    assert [p.citation_count for p in data1.publications] != [p.citation_count for p in data2.publications]


def test_synthetic_explicit_labeling():
    config = SyntheticConfig(seed=123, num_students=5, num_faculty=5, num_publications=5)
    data = SyntheticDataGenerator(config).generate()

    # Check student labeling
    for stu in data.students:
        assert stu.first_name.startswith("[SYNTHETIC]")
        assert "synthetic.university.edu" in stu.email
        assert stu.statement_of_purpose.startswith("[SYNTHETIC]")

    # Check faculty labeling
    for fac in data.faculty:
        assert fac.first_name.startswith("[SYNTHETIC]")
        assert "synthetic.university.edu" in fac.email
        assert fac.bio.startswith("[SYNTHETIC]")
        assert fac.lab_name.startswith("[SYNTHETIC]")

    # Check publication labeling
    for pub in data.publications:
        assert pub.title.startswith("[SYNTHETIC]")
        assert pub.abstract.startswith("[SYNTHETIC]")
        assert pub.doi.startswith("10.synthetic/")


def test_synthetic_relationships():
    config = SyntheticConfig(seed=42, num_students=15, num_faculty=10, num_publications=20)
    data = SyntheticDataGenerator(config).generate()

    topic_slugs = {t.slug for t in data.topics}
    faculty_emails = {f.email for f in data.faculty}

    # Verify student skills reference valid taxonomy topics
    for stu in data.students:
        for s in stu.skills:
            assert s.topic_slug in topic_slugs

    # Verify faculty skills reference valid taxonomy topics
    for fac in data.faculty:
        for s in fac.skills:
            assert s.topic_slug in topic_slugs

    # Verify publication authors reference generated faculty
    for pub in data.publications:
        assert len(pub.author_names) >= 1
        for author_email in pub.author_faculty_emails:
            assert author_email in faculty_emails


def test_synthetic_judgments_are_complete_and_topic_grounded():
    config = SyntheticConfig(
        seed=17,
        num_students=64,
        num_faculty=32,
        num_publications=128,
        num_relevance_judgments=256,
    )
    data = SyntheticDataGenerator(config).generate()

    judgments_by_student = {}
    for judgment in data.relevance_judgments:
        judgments_by_student.setdefault(judgment.student_email, []).append(judgment)

    assert len(data.relevance_judgments) == 256
    assert len(judgments_by_student) == 8
    assert all(len(judgments) == 32 for judgments in judgments_by_student.values())
    assert {judgment.relevance_grade for judgment in data.relevance_judgments} == {
        0,
        1,
        2,
        3,
    }
    assert all(
        judgment.annotator_id == "synthetic_topic_oracle"
        and "Ground truth:" in judgment.notes
        for judgment in data.relevance_judgments
    )


def test_synthetic_generator_accepts_large_benchmark_sizes():
    config = SyntheticConfig(
        num_students=1000,
        num_faculty=250,
        num_publications=3000,
        num_relevance_judgments=10000,
    )

    assert config.num_students == 1000
    assert config.num_faculty == 250
    assert config.num_publications == 3000
    assert config.num_relevance_judgments == 10000
