
project folder structure
----------------------

training_management_system/
├── apps/
│   ├── accounts/
│   ├── core/
│   └── products/
├── config/
│   ├── asgi.py
│   ├── wsgi.py
    |--- url.py
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
└── venv/


Admin Database requirement




Trainer Database Requirement
______________________________________

1. LessonPlan - Master curriculum structure for each course with phases, topics, and learning objectives
2. BatchProgress - Daily tracking of portions covered, allowing trainers to update progress against the lesson plan and note any challenges
3. ExtensionRequest - Formal system for requesting course extensions with reasons, pending topics, and admin approval workflow
4. Attendance - Daily student attendance marking with status (present/absent/late/excused) and automatic percentage calculation
5. Exam - Complete exam management with:

Multiple exam types (quiz, midterm, final, practical)
Prerequisites checking (attendance %, fees, phase completion)
Scheduling and syllabus coverage

6. ExamResult - Individual student results with:

Automatic grade calculation (A+ to F)
Eligibility verification before exam
Pass/fail determination
ERP upload tracking

7. Certificate - Certification management with:

Automatic eligibility checking (fees, attendance, completion, percentage)
Multiple certificate types
Unique certificate numbers
Snapshot of student performance at time of issuance

8. SubstituteTeaching - Track when trainers substitute for each other