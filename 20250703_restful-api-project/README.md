# RESTful API Project

This project implements a simple RESTful API using Flask. It provides an endpoint to retrieve user data.

## Project Structure

```
restful-api-project
├── src
│   ├── app.py               # Entry point of the application
│   ├── routes
│   │   └── users.py         # Defines the /v1/users endpoint
│   └── models
│       └── user.py          # User model definition
├── tests
│   └── test_users.py        # Unit tests for the /v1/users endpoint
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd restful-api-project
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/app.py
   ```

## Usage

The API provides the following endpoint:

- **GET /v1/users**: Retrieves a list of users in JSON format.

## Testing

To run the tests, use the following command:
```
pytest tests/test_users.py
```

## License

This project is licensed under the MIT License.