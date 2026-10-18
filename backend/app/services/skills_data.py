"""Extendable skill dictionary.

Structure: {category: {canonical_name: [aliases...]}}

To add a skill, add one line below, or point CUSTOM_SKILLS_PATH at a JSON file with the
same structure (see README). Aliases are normalised to the canonical name, e.g.
"JS" -> "JavaScript", "Postgres" -> "PostgreSQL".
"""

SKILL_CATALOG: dict[str, dict[str, list[str]]] = {
    "Programming": {
        "Java": [],
        "Python": [],
        "C": [],
        "C++": ["cpp"],
        "C#": ["csharp"],
        "JavaScript": ["JS", "ECMAScript"],
        "TypeScript": [],
        "SQL": [],
        "R": [],
        "Go": ["Golang"],
        "Kotlin": [],
        "PHP": [],
        "Bash": ["Shell Scripting"],
        "MATLAB": [],
        "Rust": [],
        "Scala": [],
        "Ruby": [],
    },
    "Frontend": {
        "React": ["React.js", "ReactJS"],
        "HTML": ["HTML5"],
        "CSS": ["CSS3"],
        "Tailwind CSS": ["Tailwind", "TailwindCSS"],
        "Bootstrap": [],
        "Angular": ["AngularJS"],
        "Vue.js": ["Vue", "VueJS"],
        "Redux": [],
        "Next.js": ["NextJS"],
    },
    "Backend": {
        "Node.js": ["NodeJS", "Node JS"],
        "Express": ["Express.js", "ExpressJS"],
        "FastAPI": ["Fast API"],
        "Django": [],
        "Flask": [],
        "Spring Boot": ["SpringBoot"],
        "REST API": ["REST", "RESTful", "RESTful API", "RESTful APIs", "REST APIs"],
        "GraphQL": [],
        "Microservices": ["Microservice"],
        "Kafka": ["Apache Kafka"],
        "RabbitMQ": [],
    },
    "Database": {
        "MySQL": [],
        "PostgreSQL": ["Postgres", "Postgre SQL"],
        "MongoDB": ["Mongo"],
        "Redis": [],
        "SQLite": [],
        "Oracle": ["Oracle DB"],
        "NoSQL": [],
        "Firebase": [],
    },
    "AI/ML": {
        "Machine Learning": ["ML"],
        "Deep Learning": ["DL"],
        "Natural Language Processing": ["NLP"],
        "Computer Vision": [],
        "Transformers": ["Transformer models"],
        "Scikit-learn": ["sklearn", "scikit learn"],
        "TensorFlow": ["TF"],
        "PyTorch": ["Torch"],
        "Keras": [],
        "OpenCV": [],
        "spaCy": [],
        "Hugging Face": ["HuggingFace"],
        "Pandas": [],
        "NumPy": [],
        "Generative AI": ["GenAI"],
        "LLM": ["LLMs", "Large Language Models"],
        "Data Analysis": ["Data Analytics"],
        "Data Visualization": [],
        "Statistics": [],
    },
    "Cloud/DevOps": {
        "AWS": ["Amazon Web Services"],
        "Azure": ["Microsoft Azure"],
        "Azure AI Services": ["Azure AI", "Azure Cognitive Services"],
        "GCP": ["Google Cloud", "Google Cloud Platform"],
        "Docker": [],
        "Kubernetes": ["K8s"],
        "CI/CD": ["CICD", "Continuous Integration"],
        "Jenkins": [],
        "Terraform": [],
        "Linux": [],
        "GitHub Actions": [],
    },
    "Tools": {
        "Git": [],
        "GitHub": [],
        "GitLab": [],
        "Postman": [],
        "Jira": [],
        "Figma": [],
        "Jupyter": ["Jupyter Notebook", "Jupyter Notebooks"],
        "Power BI": ["PowerBI"],
        "Tableau": [],
        "Excel": ["Microsoft Excel", "MS Excel"],
    },
    "Computer Science": {
        "Data Structures": ["DSA"],
        "Algorithms": [],
        "OOP": ["Object-Oriented Programming", "Object Oriented Programming"],
        "System Design": [],
        "ETL": [],
        "Apache Spark": ["Spark", "PySpark"],
        "Hadoop": [],
    },
    "Testing": {
        "Pytest": [],
        "JUnit": [],
        "Selenium": [],
        "Unit Testing": ["Unit Tests"],
    },
    "Practices": {
        "Agile": [],
        "Scrum": [],
    },
    "Soft Skills": {
        "Communication": ["Communication Skills"],
        "Leadership": [],
        "Teamwork": ["Team Work", "Collaboration"],
        "Problem Solving": ["Problem-Solving"],
        "Critical Thinking": [],
        "Time Management": [],
        "Adaptability": [],
    },
}

# Aliases that are common English words or very short must match with exact case,
# otherwise "rest of the team" would match REST and "excel in" would match Excel.
CASE_SENSITIVE = {
    "C", "R", "Go", "JS", "TF", "ML", "DL", "NLP", "LLM", "LLMs",
    "REST", "Express", "Excel", "Torch", "Spark", "Mongo", "Vue", "Collaboration",
}

# Technical categories (everything except these is counted as a "technology").
NON_TECH_CATEGORIES = {"Soft Skills", "Practices"}
