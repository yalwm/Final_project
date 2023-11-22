import sys
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, \
    QListWidget, QComboBox, QFileDialog, QInputDialog, QMessageBox, QMenu
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QListWidgetItem  # Add this import

class TaskManagementApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Initialize SQLite database
        self.init_db()

        # Widgets
        self.team_name_label = QLabel('Team Name:')
        self.team_name_edit = QLineEdit()
        self.goal_label = QLabel('Goal:')
        self.goal_edit = QLineEdit()

        self.add_team_button = QPushButton('Add Team')
        self.add_team_button.clicked.connect(self.add_team)

        self.member_labels = []
        self.member_edits = []

        self.add_member_button = QPushButton('+')
        self.add_member_button.clicked.connect(self.show_add_member_window)

        self.assigned_to_label = QLabel('Assigned To:')
        self.assigned_to_combo = QComboBox()
        self.populate_members_combo()

        self.task_addition_button = QPushButton('Task Addition')
        self.task_addition_button.clicked.connect(self.show_task_addition_window)

        self.task_list = QListWidget()
        self.populate_tasks()

        self.delete_task_button = QPushButton('Delete Task')
        self.delete_task_button.clicked.connect(self.delete_task)

        self.save_button = QPushButton('Save Data')
        self.save_button.clicked.connect(self.save_data)

        self.load_button = QPushButton('Load Data')
        self.load_button.clicked.connect(self.load_data)

        self.setLayout(self.setup_layout())

        self.setGeometry(100, 100, 800, 400)
        self.setWindowTitle('Task Management Application')
        self.show()

    def init_db(self):
        db = QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName('task_management.db')

        if not db.open():
            print("Error: Unable to open database")
            sys.exit(1)

        query = QSqlQuery()
        query.exec_("CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, goal TEXT)")
        query.exec_("CREATE TABLE IF NOT EXISTS team_members (id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER, name TEXT)")
        query.exec_("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, assigned_to INTEGER, done INTEGER DEFAULT 0, team_id INTEGER)")

    def add_team(self):
        team_name = self.team_name_edit.text()
        goal = self.goal_edit.text()

        query = QSqlQuery()
        query.prepare("INSERT INTO teams (name, goal) VALUES (?, ?)")
        query.bindValue(0, team_name)
        query.bindValue(1, goal)

        if query.exec_():
            team_id = query.lastInsertId()
            print("Team added successfully")
            self.populate_members_combo()
            self.populate_tasks()
        else:
            print("Error adding team:", query.lastError().text())

    def show_add_member_window(self):
        member_name, ok = QInputDialog.getText(self, "Add Team Member", "Name:")
        if ok:
            self.add_member_to_db(member_name)

    def add_member_to_db(self, member_name):
        team_id = self.get_current_team_id()

        query = QSqlQuery()
        query.prepare("INSERT INTO team_members (team_id, name) VALUES (?, ?)")
        query.bindValue(0, team_id)
        query.bindValue(1, member_name)
        if query.exec_():
            print("Team member added successfully")
            self.populate_members_combo()
        else:
            print("Error adding team member:", query.lastError().text())

    def get_current_team_id(self):
        query = QSqlQuery()
        query.exec_("SELECT MAX(id) FROM teams")
        query.next()
        return query.value(0)

    def populate_members_combo(self):
        self.assigned_to_combo.clear()

        query = QSqlQuery()
        query.exec_("SELECT * FROM team_members")

        while query.next():
            member_name = query.value(2)
            self.assigned_to_combo.addItem(member_name)

    def show_task_addition_window(self):
        task_description, ok = QInputDialog.getText(self, "Add Task", "Task Description:")
        if ok:
            items = ["To All"] + [self.assigned_to_combo.itemText(i) for i in range(self.assigned_to_combo.count())]
            assignee, ok = QInputDialog.getItem(self, "Assign To", "Assign To:", items, 0, False)
            self.add_task(task_description, assignee)

    def add_task(self, task_description, assignee):
        team_id = self.get_current_team_id()

        query = QSqlQuery()

        if assignee == "To All":
            query.prepare("INSERT INTO tasks (description, done, team_id) VALUES (?, ?, ?)")
            query.bindValue(0, task_description)
            query.bindValue(1, 0)
            query.bindValue(2, team_id)
            query.exec_()
        elif assignee:

            if assignee == "Any":

                assigned_to = None
            else:

                member_id_query = QSqlQuery()
                member_id_query.prepare("SELECT id FROM team_members WHERE name = ?")
                member_id_query.bindValue(0, assignee)
                if member_id_query.exec_() and member_id_query.next():
                    assigned_to = member_id_query.value(0)
                else:
                    print(f"Error: Unable to find ID for team member '{assignee}'")
                    return

            query.prepare("INSERT INTO tasks (description, assigned_to, done, team_id) VALUES (?, ?, ?, ?)")
            query.bindValue(0, task_description)
            query.bindValue(1, assigned_to)
            query.bindValue(2, 0)
            query.bindValue(3, team_id)
            query.exec_()
        else:
            print("Error: Invalid assignee value")

        print("Task added successfully")
        self.populate_tasks()

    def populate_tasks(self):
        self.task_list.clear()

        query = QSqlQuery()
        query.exec_("SELECT tasks.description, team_members.name, tasks.done FROM tasks LEFT JOIN team_members ON tasks.assigned_to = team_members.id")

        while query.next():
            task_description = query.value(0)
            assigned_to = query.value(1)
            done = query.value(2)

            task_item = QListWidgetItem(f"{task_description} - Assigned to: {assigned_to if assigned_to else 'Any'} - {'Done' if done else 'Not Done'}")
            self.task_list.addItem(task_item)

    def delete_task(self):
        selected_items = self.task_list.selectedItems()
        for item in selected_items:
            task_description = item.text().split('-')[0].strip()

            query = QSqlQuery()
            query.prepare("DELETE FROM tasks WHERE description = ? AND team_id = ?")
            query.bindValue(0, task_description)
            query.bindValue(1, self.get_current_team_id())

            if not query.exec_():
                print("Error deleting task:", query.lastError().text())
            else:
                print("Task deleted successfully")



        self.populate_tasks()

    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save Data', '', 'Data Files (*.dat);;All Files (*)')

        if filename:
            with open(filename, 'w') as file:
                query = QSqlQuery()

                # Save teams
                query.exec_("SELECT * FROM teams")
                while query.next():
                    team_name = query.value(1)
                    goal = query.value(2)
                    file.write(f"Team: {team_name}, Goal: {goal}\n")

                # Save team members
                query.exec_("SELECT * FROM team_members")
                while query.next():
                    member_name = query.value(2)
                    file.write(f"Team Member: {member_name}\n")

                # Save tasks
                query.exec_("SELECT tasks.description, team_members.name, tasks.done FROM tasks LEFT JOIN team_members ON tasks.assigned_to = team_members.id")
                while query.next():
                    task_description = query.value(0)
                    assigned_to = query.value(1)
                    done = query.value(2)
                    status = 'Done' if done else 'Not Done'
                    file.write(f"Task: {task_description}, Assigned to: {assigned_to if assigned_to else 'Any'}, Status: {status}\n")

            print("Data saved successfully")

    def clear_data(self):
        query = QSqlQuery()

        # Move the archiving process to a separate function
        self.archive_table_data("teams")
        self.archive_table_data("team_members")
        self.archive_table_data("tasks")

        # Delete all data from the tables
        query.exec_("DELETE FROM teams")
        query.exec_("DELETE FROM team_members")
        query.exec_("DELETE FROM tasks")

    def archive_table_data(self, table_name):
        query = QSqlQuery()
        # Execute the INSERT query
        query.exec_(f"INSERT INTO {table_name}_archive SELECT * FROM {table_name}")

        # Fetch the IDs of the archived records
        archived_record_ids = []
        query.prepare(f"SELECT id FROM {table_name}_archive")
        if query.exec_():
            while query.next():
                archived_record_id = query.value(0)
                archived_record_ids.append(archived_record_id)

        # Delete the archived records from the original table
        query.prepare(f"DELETE FROM {table_name} WHERE id IN ({', '.join(map(str, archived_record_ids))})")
        query.exec_()

    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Load Data', '', 'Data Files (*.dat);;All Files (*)')

        if filename:
            try:
                with open(filename, 'r') as file:
                    # Clear existing data
                    self.clear_data()

                    # Load data from the file
                    current_team_id = None

                    for line in file:
                        line = line.strip()

                        if line.startswith("Team:"):
                            pairs = line.split(',')
                            team_name = None
                            goal = None

                            for pair in pairs:
                                key, value = pair.split(':')
                                key = key.strip()
                                value = value.strip()

                                if key == "Team":
                                    team_name = value
                                elif key == "Goal":
                                    goal = value

                            query = QSqlQuery()
                            query.prepare("INSERT INTO teams (name, goal) VALUES (?, ?)")
                            query.bindValue(0, team_name)
                            query.bindValue(1, goal)
                            if query.exec_():
                                # Fetch the last inserted ID directly
                                current_team_id = query.lastInsertId()
                            else:
                                print("Error inserting team:", query.lastError().text())

                        elif line.startswith("Team Member:"):
                            # Handle loading team members
                            member_name = line.split(':')[-1].strip()
                            self.add_member_to_db(member_name)

                        elif line.startswith("Task:"):
                            # Handle loading tasks
                            parts = line.split(',')
                            task_description = parts[0].split(':')[-1].strip()
                            assigned_to = parts[1].split(':')[-1].strip() if len(parts) > 1 else "To All"
                            status = parts[2].split(':')[-1].strip() if len(parts) > 2 else "Not Done"

                            self.add_task(task_description, assigned_to)

                    # Load archived data for teams
                    self.load_archived_team_data()

                    self.loaded_data = True  # Set the flag to True
                    self.populate_members_combo()
                    self.populate_tasks()

            except Exception as e:
                print(f"Error loading data: {str(e)}")

    def load_archived_team_data(self):
        query = QSqlQuery()
        query.exec_("SELECT * FROM teams_archive")
        while query.next():
            team_name = query.value(1)
            goal = query.value(2)
            archived_team_query = QSqlQuery()
            archived_team_query.prepare("INSERT INTO teams (name, goal) VALUES (?, ?)")
            archived_team_query.bindValue(0, team_name)
            archived_team_query.bindValue(1, goal)
            if not archived_team_query.exec_():
                print("Error inserting archived team:", archived_team_query.lastError().text())

    def toggle_task_status(self, task_description):
        query = QSqlQuery()
        query.prepare("UPDATE tasks SET done = NOT done WHERE description = ? AND team_id = ?")
        query.bindValue(0, task_description)
        query.bindValue(1, self.get_current_team_id())

        if not query.exec_():
            print("Error toggling task status:", query.lastError().text())
        else:
            print("Task status toggled successfully")

        self.populate_tasks()

    def setup_layout(self):
        # ... (Your existing layout setup)
        layout = QVBoxLayout()

        team_layout = QVBoxLayout()
        team_layout.addWidget(self.team_name_label)
        team_layout.addWidget(self.team_name_edit)
        team_layout.addWidget(self.goal_label)
        team_layout.addWidget(self.goal_edit)
        team_layout.addWidget(self.add_team_button)

        member_layout = QVBoxLayout()
        member_layout.addWidget(QLabel('Team Members:'))
        member_layout.addWidget(self.add_member_button)

        task_layout = QVBoxLayout()
        task_layout.addWidget(self.assigned_to_label)
        task_layout.addWidget(self.assigned_to_combo)
        task_layout.addWidget(self.task_addition_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_task_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)

        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel('Task List:'))
        list_layout.addWidget(self.task_list)
        list_layout.addLayout(button_layout)

        layout.addLayout(team_layout)
        layout.addLayout(member_layout)
        layout.addLayout(task_layout)
        layout.addLayout(list_layout)

        # Add a context menu to the task list
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)

        return layout

    def show_context_menu(self, point):
        context_menu = QMenu(self)

        toggle_status_action = context_menu.addAction("Toggle Status")
        toggle_status_action.triggered.connect(self.toggle_selected_task_status)

        context_menu.exec_(self.task_list.mapToGlobal(point))

    def toggle_selected_task_status(self):
        selected_items = self.task_list.selectedItems()
        for item in selected_items:
            task_description = item.text().split('-')[0].strip()
            self.toggle_task_status(task_description)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskManagementApp()
    sys.exit(app.exec_())
