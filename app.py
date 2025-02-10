from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Todo, Directory
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, DateTimeField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CSRFProtect(app)

class TodoForm(FlaskForm):
    id = HiddenField('ID')
    title = StringField('タイトル', validators=[DataRequired()])
    description = TextAreaField('詳細')
    due_date = DateTimeField('日時 (例: 2025-03-15 14:30)', format='%Y-%m-%d %H:%M', default=datetime.utcnow)
    tag = StringField('タグ')
    directory_id = SelectField('ディレクトリ', coerce=int, choices=[])

class DirectoryForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('ディレクトリ名', validators=[DataRequired()])


@app.before_first_request
def initialize_database():
    db.create_all()

@app.route('/')
def index():
    status = request.args.get('status', 'all')
    tag_filter = request.args.get('tag', None)
    directory_filter = request.args.get('directory', None)

    query = Todo.query
    if status == 'active':
        query = query.filter_by(deleted=False, completed=False)
    elif status == 'completed':
        query = query.filter_by(deleted=False, completed=True)
    elif status == 'deleted':
        query = query.filter_by(deleted=True)

    if tag_filter:
        query = query.filter(Todo.tag.contains(tag_filter))
    if directory_filter:
        query = query.filter_by(directory_id=int(directory_filter))

    todos = query.order_by(Todo.due_date.asc()).all()
    directories = Directory.query.all()
    return render_template('index.html', todos=todos, directories=directories, status=status, tag_filter=tag_filter)

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    form = TodoForm()
    directories = Directory.query.all()
    form.directory_id.choices = [(0, '未分類')] + [(d.id, d.name) for d in directories]

    if form.validate_on_submit():
        if form.id.data:
            t = Todo.query.get(int(form.id.data))
            if not t:
                flash("指定のTodoが存在しません。", "danger")
                return redirect(url_for('index'))
        else:
            t = Todo()
        t.title = form.title.data
        t.description = form.description.data
        t.due_date = form.due_date.data
        t.tag = form.tag.data
        t.directory_id = form.directory_id.data if form.directory_id.data != 0 else None
        db.session.add(t)
        db.session.commit()
        flash("Todoが保存されました。", "success")
        return redirect(url_for('index'))
    return render_template('todo_form.html', form=form)

@app.route('/todo/<int:todo_id>/edit', methods=['GET'])
def edit_todo(todo_id):
    t = Todo.query.get_or_404(todo_id)
    form = TodoForm(obj=t)
    form.id.data = t.id
    directories = Directory.query.all()
    form.directory_id.choices = [(0, '未分類')] + [(d.id, d.name) for d in directories]
    form.directory_id.data = t.directory_id if t.directory_id else 0
    return render_template('todo_form.html', form=form)

@app.route('/todo/<int:todo_id>/toggle', methods=['POST'])
def toggle_todo(todo_id):
    t = Todo.query.get_or_404(todo_id)
    t.completed = not t.completed
    db.session.commit()
    flash("Todoの状態が更新されました。", "info")
    return redirect(url_for('index'))

@app.route('/todo/<int:todo_id>/delete', methods=['POST'])
def delete_todo(todo_id):
    t = Todo.query.get_or_404(todo_id)
    t.deleted = True
    db.session.commit()
    flash("Todoが削除されました。", "warning")
    return redirect(url_for('index'))

@app.route('/directory', methods=['GET', 'POST'])
def directory():
    form = DirectoryForm()
    if form.validate_on_submit():
        if form.id.data:
            d = Directory.query.get(int(form.id.data))
            if not d:
                flash("指定のディレクトリが存在しません。", "danger")
                return redirect(url_for('directory'))
        else:
            d = Directory()
        d.name = form.name.data
        db.session.add(d)
        db.session.commit()
        flash("ディレクトリが保存されました。", "success")
        return redirect(url_for('directory'))
    dirs = Directory.query.all()
    return render_template('directory_form.html', form=form, directories=dirs)

@app.route('/directory/<int:dir_id>/delete', methods=['POST'])
def delete_directory(dir_id):
    d = Directory.query.get_or_404(dir_id)
    for t in d.todos:
        t.directory_id = None
    db.session.delete(d)
    db.session.commit()
    flash("ディレクトリが削除されました。", "warning")
    return redirect(url_for('directory'))

@app.cli.command('init-db')
def init_db():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)