from typing import Dict, List

FIRST_NAMES = [
    "Alex", "Morgan", "Jordan", "Taylor", "Casey", "Riley", "Sam", "Chris",
    "Pat", "Jamie", "Avery", "Cameron", "Devon", "Harper", "Kai", "Quinn",
    "Rowan", "Sage", "Skyler", "Jesse", "Reese", "Finley", "Logan", "Kendall",
    "Peyton", "Emerson", "Dakota", "Hayden", "Sidney", "Parker", "Eli", "Noah"
]

LAST_NAMES = [
    "Chen", "Patel", "Smith", "Rodriguez", "Kim", "Nguyen", "Muller", "O'Connor",
    "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson",
    "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez",
    "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

DEPARTMENTS = [
    "Computer Science",
    "Electrical & Computer Engineering",
    "Data Science & AI Institute",
    "Information Science",
    "Biomedical Informatics",
]

DOMAIN_RESEARCH_TEMPLATES: Dict[str, Dict] = {
    "artificial-intelligence": {
        "lab_names": ["Intelligent Autonomous Systems Lab", "Graph Learning & Neural Dynamics Lab", "Applied Machine Intelligence Group"],
        "venues": ["NeurIPS", "ICML", "AAAI", "IJCAI"],
        "paper_titles": [
            "Scalable Graph Message-Passing for Heterogeneous Topologies",
            "Provable Sample Complexity Bounds for Deep Reinforcement Learning",
            "Geometric Deep Learning on Non-Euclidean Manifolds",
            "Self-Supervised Representation Learning for High-Dimensional State Spaces",
            "Meta-Learning Approaches to Fast Adaptation in Stochastic Environments",
        ],
        "abstracts": [
            "We propose a novel message-passing formulation that accelerates learning over massive graph topologies. Through extensive experiments, our approach reduces computational complexity by 40% while preserving predictive accuracy across benchmark molecular datasets.",
            "Sample efficiency remains a central bottleneck in continuous control reinforcement learning. In this paper, we establish tight finite-sample theoretical bounds and introduce an adaptive policy-gradient formulation that empirically demonstrates superior convergence speed.",
            "Representing structural symmetries through group equivariant neural networks is key for physics-informed machine learning. We present a generalized framework for equivariant convolutions on Riemannian manifolds with rigorous empirical validation.",
        ],
        "student_sop": [
            "My research interest lies at the intersection of deep reinforcement learning and scalable graph algorithms. I aim to develop robust agent policies capable of zero-shot transfer in dynamic multi-agent environments.",
            "I am eager to investigate geometric deep learning architectures, particularly equivariant graph neural networks applied to computational biology and topological physics modeling.",
        ],
        "project_templates": [
            ("Multi-Agent Graph Reinforcement Learning Framework", "Implemented a decentralized coordination framework using PyTorch and DGL, testing across cooperative game environments."),
            ("Benchmark Study on Geometric Graph Convolutional Networks", "Built custom CUDA-accelerated graph convolution layers and evaluated them on the Open Graph Benchmark."),
        ],
    },
    "natural-language-processing": {
        "lab_names": ["Computational Semantics & Language Lab", "Neural Foundation Models Lab", "Text Retrieval & Understanding Group"],
        "venues": ["ACL", "EMNLP", "NAACL", "COLING"],
        "paper_titles": [
            "Calibrated Retrieval-Augmented Generation for Long-Form Factuality",
            "Contextual Alignment in Massive Foundation Models via Multi-Task Steering",
            "Efficient Sparse Attention Mechanisms for Billion-Token Document Contexts",
            "Probing Latent Reasoning Trajectories in Transformer Language Models",
            "Cross-Lingual Named Entity Disambiguation via Contrastive Embeddings",
        ],
        "abstracts": [
            "Hallucination during long-form natural language generation impedes deployment in high-stakes domains. We introduce a verified retrieval-augmented pipeline that dynamically queries external knowledge bases, substantially reducing factual inconsistencies.",
            "Attention scaling poses quadratic latency challenges when processing book-length textual corpora. We present an adaptive sparse-attention kernel with linear time complexity that retains 98% downstream comprehension performance on standard benchmarks.",
            "Understanding how large language models perform complex logical reasoning is vital for safety. Through internal state probing, we uncover mechanistic attention trajectories that correlate directly with correct multi-step inference.",
        ],
        "student_sop": [
            "I want to investigate factual consistency and grounding in retrieval-augmented generation models. My objective is to prevent hallucinations when LLMs interface with scientific and legal corpora.",
            "My goal is to design parameter-efficient fine-tuning and mechanistic interpretability tools to demystify intermediate latent representations in transformer foundation models.",
        ],
        "project_templates": [
            ("RAG-Powered Academic Literature Assistant", "Developed an end-to-end question answering pipeline using LangChain, Hugging Face transformers, and FAISS vector index."),
            ("Evaluation Suite for Factuality in Generative Language Models", "Implemented automated evaluation harness measuring factual precision across 5,000 synthesized question-context pairs."),
        ],
    },
    "computer-vision": {
        "lab_names": ["Visual Computing & Perception Lab", "Applied Vision & Robotics Group", "Generative Visual Modeling Lab"],
        "venues": ["CVPR", "ICCV", "ECCV", "WACV"],
        "paper_titles": [
            "Few-Shot Semantic Segmentation in Cluttered Real-World Environments",
            "Continuous Denoising Diffusion for Real-Time High-Fidelity 3D Reconstruction",
            "Real-Time Transformer Architectures for Embedded Edge Object Detection",
            "Self-Calibrating NeRFs from Dynamic Handheld Sensor Feeds",
            "Robust Optical Flow Estimation Under Extreme Illumination Variations",
        ],
        "abstracts": [
            "Segmenting novel visual categories with minimal supervision is crucial for open-world autonomy. We demonstrate an attentive memory network that leverages self-supervised foundation features to segment previously unseen object classes from only 3 reference exemplars.",
            "Neural radiance fields often degrade when trained on jittery, uncalibrated consumer cameras. We present a bundle-adjusting formulation that simultaneously refines camera poses and neural scene volume densities in near real-time.",
            "Deploying vision transformers to constrained microcontrollers requires aggressive pruning without sacrificing edge precision. Our quantized hybrid architecture achieves 45 FPS on Raspberry Pi class hardware with negligible mAP degradation.",
        ],
        "student_sop": [
            "I am deeply committed to visual perception for edge devices. I plan to research lightweight transformer backbones for real-time semantic segmentation under harsh illumination conditions.",
            "My research goal is generative 3D reconstruction and neural radiance representations, focused on fast training and rendering for autonomous spatial computing.",
        ],
        "project_templates": [
            ("Real-Time YOLO Object Detection on Embedded Platforms", "Trained custom YOLOv8 detector using PyTorch and OpenCV, quantizing to INT8 for deployment on NVIDIA Jetson."),
            ("Neural Radiance Field Scene Synthesizer", "Implemented volumetric rendering pipeline reconstructing detailed 3D room interiors from consumer smartphone videos."),
        ],
    },
    "data-science": {
        "lab_names": ["Statistical Machine Learning Lab", "Scalable Analytics & Inference Group", "Predictive Modeling Lab"],
        "venues": ["KDD", "ICDM", "SDM", "JMLR"],
        "paper_titles": [
            "Bayesian Structural Time-Series for High-Frequency Stochastic Forecasting",
            "Robust High-Dimensional Covariance Estimation with Missing Observations",
            "Scalable Kernel Approximations for Million-Row Streaming Telemetry",
            "Causal Inference in Non-Randomized Observational Studies via Doubly Robust Estimators",
        ],
        "abstracts": [
            "Analyzing non-stationary time series with intermittent missing intervals requires flexible probabilistic modeling. We develop a variational Bayesian state-space framework capable of accurate forecasting under heavy data corruption.",
            "Estimating precision matrices in high-dimensional settings where $p \\gg n$ presents severe overfitting risks. Our regularized shrinkage estimator exhibits superior numerical stability and convergence guarantees on synthetic and empirical benchmarks.",
        ],
        "student_sop": [
            "I am passionate about statistical learning theory and causal inference. I seek to construct doubly robust estimators for complex observational datasets with unobserved confounding.",
        ],
        "project_templates": [
            ("Automated Time Series Anomaly Detector", "Engineered scalable pipeline using Pandas, Scikit-learn, and Prophet for real-time sensor anomaly detection across 100K streams."),
        ],
    },
    "cybersecurity": {
        "lab_names": ["Applied Cryptography & Privacy Lab", "Systems Security & Vulnerability Analysis Group"],
        "venues": ["USENIX Security", "IEEE S&P", "ACM CCS", "NDSS"],
        "paper_titles": [
            "Zero-Knowledge Argument Verification with Sub-Millisecond Prover Times",
            "Adversarial Evasion of Neural Intrusion Detection in Encrypted Network Streams",
            "Formal Verification of Cryptographic State Machines in Distributed Ledgers",
        ],
        "abstracts": [
            "Non-interactive zero-knowledge proofs enable privacy-preserving verification without revealing underlying witness data. We introduce a polynomial commitment scheme that minimizes prover overhead by 3.5x while keeping verification times constant.",
            "Machine learning classifiers monitoring network security remain vulnerable to adversarial payload perturbations. We formalize a gradient-free evasion attack and propose an adversarial training defense that hardens network intrusion detection systems.",
        ],
        "student_sop": [
            "My ambition is to work on applied cryptography and zero-knowledge systems. I want to build mathematically verified privacy protocols that safeguard user confidentiality in decentralized systems.",
        ],
        "project_templates": [
            ("Zero-Knowledge Identity Verification Demonstrator", "Implemented cryptographic proving system using Circom and SnarkJS, demonstrating privacy-preserving credential authentication."),
        ],
    },
    "robotics": {
        "lab_names": ["Autonomous Manipulation & Field Robotics Lab", "Robotic Perception & Control Group"],
        "venues": ["ICRA", "IROS", "RSS", "IEEE Trans. Robotics"],
        "paper_titles": [
            "Visuomotor Policy Learning for Deformable Object Robotic Manipulation",
            "Robust LiDAR-Inertial SLAM in GPS-Denied Subterranean Environments",
            "Trajectory Optimization for Quadrupedal Locomotion on Unstructured Terrains",
        ],
        "abstracts": [
            "Manipulating deformable materials such as fabrics and biological tissues remains challenging due to infinite dimensional state spaces. We train a closed-loop visuomotor diffusion policy that reliably folds and aligns flexible objects.",
            "Mobile robots navigating underground environments encounter perceptual degradation from dust, fog, and lack of visual texture. We propose a tightly coupled LiDAR-inertial odometry estimator that maintains drift-free localization over multi-kilometer traverses.",
        ],
        "student_sop": [
            "I aspire to research autonomous mobile robotics and multi-sensor SLAM fusion. My goal is to build robots capable of robust, resilient navigation in extreme, GPS-denied field environments.",
        ],
        "project_templates": [
            ("Autonomous Mobile Navigation in ROS2", "Configured Nav2 stack, simulated 3D LiDAR SLAM, and deployed path planning on a Clearpath Jackal robot platform in Gazebo."),
        ],
    },
    "human-computer-interaction": {
        "lab_names": ["Interactive Systems & Human-AI Collaboration Lab", "Accessibility & Cognitive Computing Group"],
        "venues": ["CHI", "UIST", "CSCW", "IUI"],
        "paper_titles": [
            "Designing Human-in-the-Loop Explanations for Medical Decision Support",
            "Adaptive Multimodal Interfaces for Low-Vision Accessibility in Mixed Reality",
            "Measuring Cognitive Load During Real-Time AI Pair Programming Sessions",
        ],
        "abstracts": [
            "Complex AI predictions require interpretable interfaces that do not overwhelm clinicians. Through participatory design with 30 physicians, we formulate an interactive explanation dashboard that boosts diagnostic accuracy while halving cognitive workload.",
            "Mixed reality headsets present severe accessibility barriers for visually impaired users. We develop a spatial acoustic cueing system that provides intuitive environmental awareness and object guidance without visual cues.",
        ],
        "student_sop": [
            "My research focuses on human-AI collaboration and intelligent user interfaces. I want to design transparent explanation systems that empower domain experts to audit algorithmic decisions effectively.",
        ],
        "project_templates": [
            ("Interactive Decision Support Interface", "Designed and tested a React-based cognitive dashboard visualizing AI recommendation confidences, evaluated via user study with 24 participants."),
        ],
    },
    "information-retrieval": {
        "lab_names": ["Information Retrieval & Neural Search Lab", "Recommendation & Ranking Systems Group"],
        "venues": ["SIGIR", "RecSys", "WSDM", "CIKM"],
        "paper_titles": [
            "Dense Dual-Encoder Retrieval with Learned Multi-Vector Representations",
            "Fair Multi-Objective Re-ranking in Academic Collaboration Networks",
            "Counterfactual Offline Evaluation for Long-Tail Recommendation Engines",
        ],
        "abstracts": [
            "Academic matchmaking systems must balance topical relevance with mentor availability and demographic diversity. We formulate a multi-objective re-ranking objective using reciprocal rank fusion that achieves optimal trade-offs between precision and fairness.",
            "Evaluating recommender algorithms using biased historical interaction logs leads to severe Matthew effects. We apply inverse propensity weighting and doubly robust estimators to conduct unbiased offline ranking evaluations.",
        ],
        "student_sop": [
            "I am fascinated by modern information retrieval, dense bi-encoder architectures, and recommendation systems. My goal is to create scalable, explainable matchmaking platforms that connect researchers with complementary interests.",
        ],
        "project_templates": [
            ("Semantic Neural Search Engine", "Built a vector search engine over 50,000 research papers using Sentence Transformers, pgvector, and FastAPI with sub-10ms query latency."),
        ],
    },
    "cloud-computing": {
        "lab_names": ["Cloud Systems & Resilience Lab", "Distributed Platforms Group"],
        "venues": ["SoCC", "Middleware", "IEEE CLOUD", "USENIX ATC"],
        "paper_titles": [
            "Cost-Aware Autoscaling for Bursty Cloud-Native Workloads",
            "Fault-Tolerant State Management Across Serverless Functions",
            "Policy Verification for Multi-Tenant Kubernetes Clusters",
        ],
        "abstracts": [
            "Cloud-native services experience rapidly changing workloads and strict latency budgets. We evaluate a predictive autoscaling controller across distributed traces and report resource use, tail latency, and recovery behavior.",
            "Serverless applications often distribute state across short-lived functions. We compare durable state-management strategies under retry, concurrency, and regional failure scenarios.",
        ],
        "student_sop": [
            "I want to study dependable cloud computing, distributed systems, and resource-efficient orchestration for cloud-native applications.",
        ],
        "project_templates": [
            ("Kubernetes Workload Autoscaler", "Implemented and evaluated a reproducible autoscaling controller using containerized workloads and latency measurements."),
        ],
    },
    "bioinformatics": {
        "lab_names": ["Computational Genomics Lab", "Systems Biology & Data Science Group"],
        "venues": ["Bioinformatics", "Genome Biology", "BMC Bioinformatics", "RECOMB"],
        "paper_titles": [
            "Robust Variant Prioritization Across Diverse Genomic Cohorts",
            "Single-Cell Expression Analysis with Batch-Aware Models",
            "Scalable Sequence Alignment for Comparative Genomics",
        ],
        "abstracts": [
            "Genomic studies require reproducible analysis of heterogeneous cohorts. We evaluate statistical variant-prioritization methods with held-out data and report calibration across population subgroups.",
            "Single-cell expression measurements contain technical and biological variation. We compare batch-aware representations for identifying reproducible cell populations across independent datasets.",
        ],
        "student_sop": [
            "My research goal is to develop reproducible computational genomics and bioinformatics methods for biological sequence and single-cell data.",
        ],
        "project_templates": [
            ("Reproducible Genomic Variant Analysis", "Built a documented sequence-analysis workflow with quality checks and held-out validation on public benchmark data."),
        ],
    },
}
