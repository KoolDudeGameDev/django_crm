from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .forms import SignUpForm, AddRecordForm, NoteForm
from .models import Record, Notes

def home(request):
    records = Record.objects.all().order_by("id")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    if query:
        records = records.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    if status:
        records = records.filter(status=status)

    context = {
        "records": records,
        "query": query,
        "selected_status": status,
        "status_choices": Record.STATUS_CHOICES,
    }

    # Check to see if logging in
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect("home")
        else:
            messages.success(request, "Invalid credentials. Please try again.")
            return redirect("home")
    
    else:
        return render(request, "home.html", context) 


def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("home")


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            # Authenticate and login
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have successfully registered.")
            return redirect("home")
        
    else:
        form = SignUpForm()
        return render(request, "register.html", {"form": form})
    
    return render(request, "register.html", {"form": form})


def customer_record(request, pk):
    if request.user.is_authenticated:
        # Look up the customer record
        customer_record = Record.objects.get(id=pk)
        notes = customer_record.notes.all().order_by("-date")

        if request.method == "POST":
            if "delete_note" not in request.POST:
                # Handle the Note form (add new note)
                note_form = NoteForm(request.POST)

                # If the form is valid, save the note
                if note_form.is_valid():
                    note = note_form.save(commit=False)
                    note.record = customer_record  # Link the note to the customer
                    note.save()

                    # Redirect back to the same page to display the newly added note
                    return redirect("record", pk=pk)

            else:
                # Handle Note deletion
                note_id = request.POST.get("note_id")
                if note_id:
                    note = Notes.objects.get(id=note_id)
                    if note.record == customer_record:
                        note.delete()
                return redirect("record", pk=pk)

        else:
            note_form = NoteForm()

        # Render the page with customer info, notes, and the form
        return render(request, "record.html", {
            "customer_record": customer_record,
            "notes": notes,
            "note_form": note_form
        })
    
    else:
        messages.success(request, "You must be logged in to view this page.")
        return redirect("home")
    

def update_record(request, pk):
    if request.user.is_authenticated:
        current_customer = Record.objects.get(id=pk)

        if request.method == "POST":
            # Process the customer update form
            form = AddRecordForm(request.POST, instance=current_customer)
            
            if form.is_valid():
                # Save the updated customer record
                form.save()
                # Redirect after saving
                return redirect("record", pk=pk)

        else:
            form = AddRecordForm(instance=current_customer)

        return render(request, "update_record.html", {
            "form": form,
            "customer_record": current_customer
        })
    
    else:
        messages.success(request, "You must be logged in to view page.")
        return redirect("home")


def delete_record(request, pk):
    if request.user.is_authenticated:
        delete_it = Record.objects.get(id=pk)
        delete_it.delete()
        messages.success(request, "Record deleted successfully.")
        return redirect("home")
    else:
        messages.success(request, "You must be logged in to delete record.")
        return redirect("home")


def add_record(request):
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added")
                return redirect("home")
        return render(request, "add_record.html", {"form":form})        
    else:
        messages.success(request, "You must be logged in to create")
        return redirect("home")
            



