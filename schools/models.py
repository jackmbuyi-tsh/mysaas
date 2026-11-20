from django.db import models

from tenants.models import Employee, TenantScopedModel


class Building(TenantScopedModel):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolYear(TenantScopedModel):
    label = models.CharField(max_length=20)  # e.g. "2026-2027"
    starts_on = models.DateField()
    ends_on = models.DateField()

    class Meta(TenantScopedModel.Meta):
        ordering = ["-starts_on"]

    def __str__(self):
        return self.label


class SchoolClass(TenantScopedModel):
    name = models.CharField(max_length=50)  # e.g. "6e A"
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, related_name="classes")
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, null=True, blank=True, related_name="classes"
    )
    titular = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="titular_of"
    )

    class Meta(TenantScopedModel.Meta):
        ordering = ["name"]
        verbose_name_plural = "school classes"

    def __str__(self):
        return f"{self.name} ({self.year})"


class Parent(TenantScopedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Pupil(TenantScopedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name="pupils"
    )
    # A pupil can have several parents; a parent can have several children.
    parents = models.ManyToManyField(Parent, blank=True, related_name="children")

    class Meta(TenantScopedModel.Meta):
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Course(TenantScopedModel):
    name = models.CharField(max_length=100)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="courses")
    teacher = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    max_points = models.PositiveSmallIntegerField(default=20)

    def __str__(self):
        return f"{self.name} – {self.school_class.name}"


class Grade(TenantScopedModel):
    class Term(models.IntegerChoices):
        T1 = 1, "1er trimestre"
        T2 = 2, "2e trimestre"
        T3 = 3, "3e trimestre"

    pupil = models.ForeignKey(Pupil, on_delete=models.CASCADE, related_name="grades")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="grades")
    term = models.PositiveSmallIntegerField(choices=Term.choices)
    points = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta(TenantScopedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "pupil", "course", "term"], name="one_grade_per_term"
            )
        ]

    def __str__(self):
        return f"{self.pupil} – {self.course.name} T{self.term}: {self.points}"
