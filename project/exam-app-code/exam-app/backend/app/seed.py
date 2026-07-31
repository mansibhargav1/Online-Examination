from sqlalchemy.orm import Session

from app.config import settings
from app.models import Exam, Option, Question, Role, User
from app.security import hash_password

DEMO_INSTRUCTIONS = """1. This paper has 5 questions. Each one appears on its own screen.
2. You get 2 minutes per question. The clock starts the moment the question loads.
3. Once you move on, you cannot come back. Answers are final.
4. A correct answer scores +4. A wrong answer scores -1. Leaving it blank scores 0.
5. If the timer reaches zero, the question is recorded as unattempted.
6. The clock runs on the server. Refreshing the page will not reset it.
7. Keep this tab open. Closing it does not pause the timer."""

DEMO_QUESTIONS = [
    ("Which data structure uses First-In-First-Out ordering?",
     [("Queue", True), ("Stack", False), ("Binary tree", False), ("Hash map", False)]),
    ("What is the time complexity of binary search on a sorted array of n elements?",
     [("O(log n)", True), ("O(n)", False), ("O(n log n)", False), ("O(1)", False)]),
    ("In relational databases, which key uniquely identifies each row in a table?",
     [("Primary key", True), ("Foreign key", False), ("Candidate index", False), ("Composite view", False)]),
    ("Which HTTP status code means the request succeeded and a resource was created?",
     [("201", True), ("200", False), ("204", False), ("301", False)]),
    ("Which of these is NOT a property of a database transaction under ACID?",
     [("Availability", True), ("Atomicity", False), ("Isolation", False), ("Durability", False)]),
]

DEVOPS_INSTRUCTIONS = """1. This paper has 20 questions. Each one appears on its own screen.
2. You get 2 minutes per question. The clock starts the moment the question loads.
3. Once you move on, you cannot come back. Answers are final.
4. A correct answer scores +4. A wrong answer scores -1. Leaving it blank scores 0.
5. If the timer reaches zero, the question is recorded as unattempted.
6. The clock runs on the server. Refreshing the page will not reset it.
7. Keep this tab open. Closing it does not pause the timer."""

DEVOPS_QUESTIONS = [
    ("Which command is used to create a new Git branch and switch to it in one step?",
     [("git checkout -b", True), ("git branch -new", False), ("git switch --create-only", False), ("git make branch", False)]),
    ("In Docker, which instruction in a Dockerfile defines the command that runs when the container starts?",
     [("CMD", True), ("RUN", False), ("COPY", False), ("FROM", False)]),
    ("What is the default configuration file used by Kubernetes to define a deployment?",
     [("A YAML manifest", True), ("An INI file", False), ("A TOML file", False), ("An XML descriptor", False)]),
    ("Which tool is primarily used for infrastructure as code to provision cloud resources declaratively?",
     [("Terraform", True), ("Jenkins", False), ("Nagios", False), ("Ansible Tower", False)]),
    ("In a CI/CD pipeline, what does the 'CD' most commonly stand for?",
     [("Continuous Delivery / Deployment", True), ("Central Distribution", False), ("Code Debugging", False), ("Container Definition", False)]),
    ("Which command lists all running Docker containers?",
     [("docker ps", True), ("docker ls", False), ("docker running", False), ("docker list", False)]),
    ("In Kubernetes, what is the smallest deployable unit that you can create and manage?",
     [("Pod", True), ("Node", False), ("Container", False), ("Service", False)]),
    ("Which of these is a configuration management tool that uses an agentless, push-based model over SSH?",
     [("Ansible", True), ("Puppet", False), ("Chef", False), ("SaltStack (master mode)", False)]),
    ("What does the 'kubectl get pods' command do?",
     [("Lists the pods in the current namespace", True), ("Deletes all pods", False), ("Creates a new pod", False), ("Restarts the cluster", False)]),
    ("In Git, which command downloads changes from a remote without merging them into your working branch?",
     [("git fetch", True), ("git pull", False), ("git clone", False), ("git commit", False)]),
    ("Which port does the Kubernetes API server listen on by default (HTTPS)?",
     [("6443", True), ("8080", False), ("443", False), ("22", False)]),
    ("What is the purpose of a reverse proxy like Nginx in front of application servers?",
     [("Routing and load balancing incoming requests", True), ("Compiling application code", False), ("Storing database records", False), ("Encrypting local disk volumes", False)]),
    ("In Docker, what is the difference between an image and a container?",
     [("An image is a read-only template; a container is a running instance of it", True), ("They are exactly the same thing", False), ("A container is a template; an image is a running instance", False), ("An image runs, a container stores logs", False)]),
    ("Which AWS service is commonly used for object storage?",
     [("S3", True), ("EC2", False), ("RDS", False), ("Lambda", False)]),
    ("What does 'idempotent' mean in the context of configuration management?",
     [("Running an operation multiple times yields the same result", True), ("An operation can only run once", False), ("An operation always fails on retry", False), ("An operation requires manual approval", False)]),
    ("Which command applies a Kubernetes configuration from a file?",
     [("kubectl apply -f", True), ("kubectl run -f", False), ("kubectl set -f", False), ("kubectl deploy -f", False)]),
    ("In monitoring, what is the primary role of Prometheus?",
     [("Collecting and storing time-series metrics", True), ("Managing container images", False), ("Provisioning cloud servers", False), ("Serving static web pages", False)]),
    ("What is a 'blue-green deployment' strategy designed to achieve?",
     [("Zero-downtime releases by switching between two environments", True), ("Encrypting network traffic", False), ("Reducing container image size", False), ("Automatic database sharding", False)]),
    ("Which file format is commonly used for Ansible playbooks?",
     [("YAML", True), ("JSON only", False), ("XML", False), ("CSV", False)]),
    ("In a Jenkins pipeline, what file typically defines the pipeline stages as code?",
     [("Jenkinsfile", True), ("pipeline.xml", False), ("build.gradle", False), ("Makefile", False)]),
]


def seed(db: Session) -> None:
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not admin:
        db.add(User(
            full_name="System Administrator",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=Role.admin,
        ))
        db.commit()
        print(f"[seed] admin account created: {settings.ADMIN_EMAIL}")

    if not settings.SEED_DEMO_EXAM:
        return
    if db.query(Exam).count():
        return

    exam = Exam(
        title="Computer Science Fundamentals",
        description="A short screening paper covering data structures, algorithms, databases and web basics.",
        instructions=DEMO_INSTRUCTIONS,
        seconds_per_question=settings.QUESTION_TIME_SECONDS,
        marks_correct=4,
        marks_wrong=-1,
        marks_unattempted=0,
    )
    db.add(exam)
    db.flush()

    for qi, (text, opts) in enumerate(DEMO_QUESTIONS):
        q = Question(exam_id=exam.id, text=text, order_index=qi)
        db.add(q)
        db.flush()
        # Shuffle deterministically so the correct answer isn't always first.
        ordered = opts[qi % len(opts):] + opts[:qi % len(opts)]
        for oi, (otext, is_correct) in enumerate(ordered):
            db.add(Option(question_id=q.id, text=otext, is_correct=is_correct, order_index=oi))

    devops_exam = Exam(
        title="devops engineer MCQ",
        description="A screening paper covering CI/CD, containers, Kubernetes, infrastructure as code and monitoring.",
        instructions=DEVOPS_INSTRUCTIONS,
        seconds_per_question=settings.QUESTION_TIME_SECONDS,
        marks_correct=4,
        marks_wrong=-1,
        marks_unattempted=0,
    )
    db.add(devops_exam)
    db.flush()

    for qi, (text, opts) in enumerate(DEVOPS_QUESTIONS):
        q = Question(exam_id=devops_exam.id, text=text, order_index=qi)
        db.add(q)
        db.flush()
        # Shuffle deterministically so the correct answer isn't always first.
        ordered = opts[qi % len(opts):] + opts[:qi % len(opts)]
        for oi, (otext, is_correct) in enumerate(ordered):
            db.add(Option(question_id=q.id, text=otext, is_correct=is_correct, order_index=oi))

    db.commit()
    print("[seed] demo exam created")
