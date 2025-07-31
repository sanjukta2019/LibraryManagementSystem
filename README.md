Project Name: Library Management System
Description:
It is a multi-user application, one librarian and multiple users. There is the librarian
dashboard to add e-books and sections and view requests and the user dashboard to view
available books and make a request.
Technologies used:
Flask, python for backend, sqlalchemy for database and html (Bootstrap) for frontend.

Database structure:
The models and routes are in app.py.
The database file is database.db is in instance folder. The html files are in templates folder.
Models include the following tables:
User, Section, Books, Request and Feedback. For declaring the one-to-many relationship
among the tables used ‘ForeignKey’. To show the many-to-many relationships, applied
'backref’ on the tables.
Sessions are implemented, from flask session is imported. If user_id in session, user will
have access to the respective pages. When user logs out, user_id is removed from sessions.
To restrict redundancy of code used decorators(passing a function as argument to another
function). Created two functions auth_required and librarian_required to restrict the routes
without authentication.
Applied Jinja template inheritance, used extends tag to extend one template from another.
Created the layout template and used the template in several html pages applying the
extends tag in jinja.
Flash messages used to highlight the error messages.
For styling purpose used bootstrap.

About the app:
The user registers and on logging in using the credentials, sees the available books and
requests for a book mentioning the number of days requested for. The user can request for a
maximum 5 books. There is the search functionality on the user dashboard to search by
section name, book name or author name. On the profile page, the user can view the
approved books and on clicking on read option, it redirects to an html page to read. User can
submit feedback.
The librarian can add, edit or delete sections and books. Librarian will view request, may
approve, reject or revoke access to the book on the return date. The librarian can view the
user feedbacks.

