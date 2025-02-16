from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'todos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(100))
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=2)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        todo_title = request.form.get('title')
        todo_description = request.form.get('description', '')
        todo_priority = request.form.get('priority', 2, type=int)

        # Validate required fields
        if not todo_title:
            flash('Task title is required', 'danger')
            return redirect(url_for('home'))
            
        if len(todo_description) > 300:
            flash('Description cannot exceed 300 characters', 'danger')
            return redirect(url_for('home'))

        # Create new task
        new_todo = Todo(
            title=todo_title,
            description=todo_description,
            priority=todo_priority,
            completed=False,
            date_created=datetime.utcnow()
        )

        try:
            db.session.add(new_todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error saving task to database', 'danger')

        return redirect(url_for('home'))

    # GET request handling remains same
    active_todos = Todo.query.filter_by(completed=False).order_by(Todo.date_created.desc()).all()
    completed_todos = Todo.query.filter_by(completed=True).order_by(Todo.date_completed.desc()).all()
    return render_template('index.html', 
                         active_todos=active_todos,
                         completed_todos=completed_todos)

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    try:
        todo = Todo.query.get_or_404(id)
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False}), 500

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    todo = Todo.query.get_or_404(id)
    if 'completed' in request.json:
        todo.completed = request.json['completed']
        todo.date_completed = datetime.utcnow() if request.json['completed'] else None
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete-completed', methods=['POST'])
def delete_completed():
    try:
        Todo.query.filter_by(completed=True).delete()
        db.session.commit()
        flash('All completed tasks deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting completed tasks', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)

