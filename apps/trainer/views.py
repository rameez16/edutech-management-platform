from django.shortcuts import render

def dashboard(request):
    """Dashboard view"""
    context = {
        'page_title': 'Dashboard',
    }
    return render(request, 'trainer/dashboard/overview.html', context)

def trainer_profile(request):
    return render(request, "trainer/profile.html")

# Static batches & students data
BATCHES = {
    1: {
        "id": 1,
        "name": "DS-433",
        "course": "Data Science",
        "timing": "7:00 – 8:00 AM",
        "duration": "60 Days",
        "start_date": "24/12/2024",
        "end_date": "24/02/2025",
        "classes_completed": "15 / 60",
        "progress": 25,
        "students": [
            {"id": 1, "name": "Arun Kumar", "phone": "9876543210", "status": "Active", "email": "arun@gmail.com", "joined_on": "10 Jan 2025"},
            {"id": 2, "name": "Priya Sharma", "phone": "9123456789", "status": "Active", "email": "priya@gmail.com", "joined_on": "15 Jan 2025"},
            {"id": 3, "name": "Rahul Verma", "phone": "9012345678", "status": "Inactive", "email": "rahul@gmail.com", "joined_on": "20 Jan 2025"},
        ]
    },
    2: {
        "id": 2,
        "name": "WD-221",
        "course": "Web Development",
        "timing": "10:00 – 11:30 AM",
        "duration": "45 Days",
        "start_date": "10/01/2025",
        "end_date": "25/02/2025",
        "classes_completed": "20 / 45",
        "progress": 45,
        "students": [
            {"id": 4, "name": "Ankit Singh", "phone": "9011223344", "status": "Active", "email": "ankit@gmail.com", "joined_on": "11 Jan 2025"},
            {"id": 5, "name": "Sneha Kapoor", "phone": "9988776655", "status": "Active", "email": "sneha@gmail.com", "joined_on": "13 Jan 2025"},
            {"id": 6, "name": "Rohan Das", "phone": "9876543211", "status": "Inactive", "email": "rohan@gmail.com", "joined_on": "18 Jan 2025"},
        ]
    },
}

def my_batches(request):
    context = {
        "batches": BATCHES.values()
    }
    return render(request, "trainer/mybatches/batchlist.html", context)


def batch_overview_view(request, batch_id):
    batch = BATCHES.get(batch_id)
    active_students = sum(1 for s in batch["students"] if s["status"] == "Active")
    inactive_students = sum(1 for s in batch["students"] if s["status"] == "Inactive")
    
    context = {
        "batch_id": batch_id,
        "batch": batch,
        "active_tab": "overview",
    }
    return render(request, "trainer/mybatches/overview.html", context)


def batch_students_view(request, batch_id):
    batch = BATCHES.get(batch_id)
    context = {
        "batch_id": batch_id,
        "batch": batch,
        "students": batch["students"],
        "active_tab": "students",
    }
    return render(request, "trainer/mybatches/students.html", context)


def student_detail_view(request, batch_id, student_id):
    batch = BATCHES.get(batch_id)
    student = next((s for s in batch["students"] if s["id"] == student_id), None)
    context = {
        "batch_id": batch_id,
        "student": student,
        "active_tab": "students",
    }
    return render(request, "trainer/mybatches/student_detail.html", context)



