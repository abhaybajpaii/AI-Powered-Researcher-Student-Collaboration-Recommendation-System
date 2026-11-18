from typing import Dict, List, Optional
from backend.app.ingestion.schemas import TopicSkillIngestDTO

# Core academic research domains with hierarchical topics, methodologies, and technical skills
ACADEMIC_TAXONOMY_TREE: List[Dict] = [
    # 1. Artificial Intelligence
    {
        "name": "Artificial Intelligence",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Foundations, algorithms, and applications of autonomous rational agents.",
        "children": [
            {
                "name": "Machine Learning",
                "category": "RESEARCH_TOPIC",
                "description": "Algorithms that learn predictive patterns and representations from data.",
                "children": [
                    {"name": "Statistical Learning", "category": "METHODOLOGY", "description": "Generalization, model selection, and learning theory."},
                ],
            },
            {
                "name": "Deep Learning",
                "category": "RESEARCH_TOPIC",
                "description": "Multi-layer neural network representations and training dynamics.",
                "children": [
                    {"name": "Graph Neural Networks", "category": "METHODOLOGY", "description": "Message-passing networks for non-Euclidean graph topologies."},
                    {"name": "Reinforcement Learning", "category": "METHODOLOGY", "description": "Markov decision processes, policy gradients, and Q-learning."},
                    {"name": "PyTorch", "category": "TECHNICAL_SKILL", "description": "Open-source deep learning tensor library."},
                    {"name": "TensorFlow", "category": "TECHNICAL_SKILL", "description": "End-to-end open source platform for machine learning."},
                ],
            },
            {
                "name": "Explainable AI (XAI)",
                "category": "RESEARCH_TOPIC",
                "description": "Interpretable models, attribution methods, and transparent decision-making.",
                "children": [
                    {"name": "SHAP & LIME", "category": "METHODOLOGY", "description": "Feature attribution and local surrogate explanation frameworks."},
                ],
            },
        ],
    },
    # 2. Natural Language Processing
    {
        "name": "Natural Language Processing",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Computational linguistics, text comprehension, and natural language generation.",
        "children": [
            {
                "name": "Large Language Models",
                "category": "RESEARCH_TOPIC",
                "description": "Pre-trained transformer foundation models and alignment.",
                "children": [
                    {"name": "Retrieval-Augmented Generation (RAG)", "category": "METHODOLOGY", "description": "Grounding generative models with external vector search corpora."},
                    {"name": "Hugging Face Transformers", "category": "TECHNICAL_SKILL", "description": "State-of-the-art NLP library for transformer architectures."},
                    {"name": "Prompt Engineering", "category": "METHODOLOGY", "description": "In-context learning, chain-of-thought, and instruction tuning."},
                ],
            },
            {
                "name": "Computational Semantics",
                "category": "RESEARCH_TOPIC",
                "description": "Entity linking, semantic parsing, and knowledge graphs.",
                "children": [
                    {"name": "Named Entity Recognition (NER)", "category": "METHODOLOGY", "description": "Information extraction identifying named entities in text."},
                ],
            },
        ],
    },
    # 3. Computer Vision
    {
        "name": "Computer Vision",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Algorithms for visual perception, video understanding, and 3D reconstruction.",
        "children": [
            {
                "name": "Object Detection & Segmentation",
                "category": "RESEARCH_TOPIC",
                "description": "Bounding box localization and pixel-level semantic segmentation.",
                "children": [
                    {"name": "YOLO Architectures", "category": "METHODOLOGY", "description": "Real-time single-stage bounding box object detectors."},
                    {"name": "OpenCV", "category": "TECHNICAL_SKILL", "description": "Real-time computer vision and image processing library."},
                ],
            },
            {
                "name": "Generative Vision Models",
                "category": "RESEARCH_TOPIC",
                "description": "Diffusion models, NeRFs, and image synthesis.",
                "children": [
                    {"name": "Diffusion Models", "category": "METHODOLOGY", "description": "Denoising score-based generative visual synthesis."},
                ],
            },
        ],
    },
    # 4. Data Science
    {
        "name": "Data Science",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Statistical inference, big data processing, and predictive analytics.",
        "children": [
            {
                "name": "Statistical Machine Learning",
                "category": "RESEARCH_TOPIC",
                "description": "Non-parametric estimation, Bayesian modeling, and dimensional reduction.",
                "children": [
                    {"name": "Pandas & NumPy", "category": "TECHNICAL_SKILL", "description": "Tabular data manipulation and vector computation in Python."},
                    {"name": "Scikit-Learn", "category": "TECHNICAL_SKILL", "description": "Classical machine learning estimators and evaluation pipelines."},
                ],
            },
            {
                "name": "Time Series Forecasting",
                "category": "RESEARCH_TOPIC",
                "description": "Sequential modeling, ARIMA, and temporal state-space models.",
                "children": [
                    {"name": "Prophet & Temporal Fusion Transformers", "category": "METHODOLOGY", "description": "Decomposable and attention-based time-series forecasting."},
                ],
            },
        ],
    },
    # 5. Cybersecurity
    {
        "name": "Cybersecurity",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Network security, cryptography, and vulnerability assessment.",
        "children": [
            {
                "name": "Applied Cryptography",
                "category": "RESEARCH_TOPIC",
                "description": "Cryptographic primitives, post-quantum crypto, and privacy-preserving computation.",
                "children": [
                    {"name": "Zero-Knowledge Proofs", "category": "METHODOLOGY", "description": "Succinct non-interactive cryptographic proof arguments."},
                ],
            },
            {
                "name": "Adversarial Machine Learning",
                "category": "RESEARCH_TOPIC",
                "description": "Model evasion, data poisoning, and model inversion defense.",
                "children": [
                    {"name": "Adversarial Robustness Testing", "category": "METHODOLOGY", "description": "Projected gradient descent and boundary perturbation audits."},
                ],
            },
        ],
    },
    # 6. Robotics
    {
        "name": "Robotics",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Autonomous manipulation, mobile robotics, and cyber-physical systems.",
        "children": [
            {
                "name": "Autonomous Navigation",
                "category": "RESEARCH_TOPIC",
                "description": "Simultaneous localization and mapping, path planning, and obstacle avoidance.",
                "children": [
                    {"name": "ROS2 (Robot Operating System)", "category": "TECHNICAL_SKILL", "description": "Middleware communication framework for robotic sensors and actuators."},
                    {"name": "SLAM Algorithms", "category": "METHODOLOGY", "description": "Visual and LiDAR simultaneous localization and mapping."},
                ],
            },
        ],
    },
    # 7. Human-Computer Interaction
    {
        "name": "Human-Computer Interaction",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "User experience research, accessibility, and interactive interface design.",
        "children": [
            {
                "name": "Intelligent User Interfaces",
                "category": "RESEARCH_TOPIC",
                "description": "Adaptive interfaces, mixed reality, and cognitive load reduction.",
                "children": [
                    {"name": "Usability Testing & Qualitative Coding", "category": "METHODOLOGY", "description": "Rigorous cognitive walkthroughs and thematic interview analysis."},
                ],
            },
        ],
    },
    # 8. Information Retrieval
    {
        "name": "Information Retrieval",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Search engines, neural ranking, and recommender systems.",
        "children": [
            {
                "name": "Recommender Systems",
                "category": "RESEARCH_TOPIC",
                "description": "Collaborative filtering, hybrid ranking, and matrix factorization.",
                "children": [
                    {"name": "Vector Similarity Search", "category": "METHODOLOGY", "description": "Approximate nearest neighbor retrieval with HNSW and IVFFlat."},
                ],
            },
            {
                "name": "Dense Retrieval & Ranking",
                "category": "RESEARCH_TOPIC",
                "description": "Bi-encoders, cross-encoders, and reciprocal rank fusion.",
                "children": [
                    {"name": "Sentence Transformers", "category": "TECHNICAL_SKILL", "description": "Siamese neural networks generating dense sentence embeddings."},
                ],
            },
        ],
    },
    # 9. Cloud Computing
    {
        "name": "Cloud Computing",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Distributed cloud platforms, scalable systems, and cloud-native computing.",
        "children": [
            {
                "name": "Distributed Systems",
                "category": "RESEARCH_TOPIC",
                "description": "Fault-tolerant distributed storage, services, and consensus.",
                "children": [
                    {"name": "Kubernetes", "category": "TECHNICAL_SKILL", "description": "Container orchestration for distributed applications."},
                    {"name": "Serverless Computing", "category": "METHODOLOGY", "description": "Event-driven application execution on managed infrastructure."},
                ],
            },
            {
                "name": "Cloud Security",
                "category": "RESEARCH_TOPIC",
                "description": "Identity, access, and privacy protections for cloud workloads.",
                "children": [
                    {"name": "Infrastructure as Code", "category": "TECHNICAL_SKILL", "description": "Declarative provisioning and configuration of infrastructure."},
                ],
            },
        ],
    },
    # 10. Bioinformatics
    {
        "name": "Bioinformatics",
        "category": "DOMAIN",
        "parent_slug": None,
        "description": "Computational methods for biological data and biomedical discovery.",
        "children": [
            {
                "name": "Computational Genomics",
                "category": "RESEARCH_TOPIC",
                "description": "Statistical analysis of genomic variation and gene expression.",
                "children": [
                    {"name": "Sequence Alignment", "category": "METHODOLOGY", "description": "Comparative analysis of biological nucleotide and protein sequences."},
                    {"name": "Biopython", "category": "TECHNICAL_SKILL", "description": "Python tools for biological sequence analysis."},
                ],
            },
            {
                "name": "Systems Biology",
                "category": "RESEARCH_TOPIC",
                "description": "Modeling interactions among genes, proteins, and biological pathways.",
                "children": [
                    {"name": "Single-Cell Analysis", "category": "METHODOLOGY", "description": "Computational analysis of single-cell molecular measurements."},
                ],
            },
        ],
    },
]


def flatten_taxonomy_tree() -> List[TopicSkillIngestDTO]:
    """Flattens the nested academic taxonomy tree into a list of TopicSkillIngestDTOs."""
    results: List[TopicSkillIngestDTO] = []

    def _traverse(node: Dict, parent_slug: Optional[str] = None):
        dto = TopicSkillIngestDTO(
            name=node["name"],
            category=node["category"],
            parent_slug=parent_slug,
            description=node.get("description"),
        )
        results.append(dto)
        for child in node.get("children", []):
            _traverse(child, parent_slug=dto.slug)

    for root_node in ACADEMIC_TAXONOMY_TREE:
        _traverse(root_node, parent_slug=None)

    return results
