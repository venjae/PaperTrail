// Student Assignment Tracker - Skeleton

// Data structures
const Assignment = {
  id: null,
  title: "",
  course: "",
  dueDate: null,
  priority: "medium", // low, medium, high
  status: "pending", // pending, in-progress, completed
  notes: ""
};

const Course = {
  id: null,
  name: "",
  code: "",
  color: "#000000"
};

// State management
const state = {
  assignments: [],
  courses: [],
  filter: "all", // all, pending, completed, overdue
  sortBy: "dueDate"
};

// UI Components (to be implemented)
function renderAssignmentList() {}
function renderAssignmentForm() {}
function renderCourseList() {}
function renderDashboard() {}

// CRUD Operations
function addAssignment(assignment) {}
function updateAssignment(id, updates) {}
function deleteAssignment(id) {}
function getAssignmentById(id) {}

// Helper functions
function getAssignmentsByCourse(courseId) {}
function getOverdueAssignments() {}
function getUpcomingAssignments(days) {}

// Event handlers
function handleAddAssignment() {}
function handleEditAssignment() {}
function handleDeleteAssignment() {}
function handleToggleStatus() {}
function handleFilterChange() {}
function handleSortChange() {}