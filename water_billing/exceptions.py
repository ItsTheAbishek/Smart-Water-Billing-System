# exceptions.py
# Custom exception classes for the Smart Water Billing System

class WaterBillingError(Exception):
    """Base exception class for all billing system errors."""
    pass


class InvalidCategoryError(WaterBillingError):
    """Raised when a customer's category is not recognised by the system."""
    def __init__(self, category):
        self.category = category
        super().__init__(
            f"Invalid customer category: '{category}'. "
            f"Accepted categories are: Residential, Commercial, Industrial."
        )


class NegativeConsumptionError(WaterBillingError):
    """Raised when a consumption value is negative."""
    def __init__(self, customer_id, value):
        self.customer_id = customer_id
        self.value = value
        super().__init__(
            f"Customer '{customer_id}' has a negative consumption value: {value} kL. "
            f"Consumption must be zero or greater."
        )


class MissingFieldError(WaterBillingError):
    """Raised when a required field is missing from a customer record."""
    def __init__(self, customer_id, field):
        self.customer_id = customer_id
        self.field = field
        super().__init__(
            f"Missing required field '{field}' for customer '{customer_id}'."
        )


class MalformedConfigError(WaterBillingError):
    """Raised when the JSON tariff configuration file is malformed or unreadable."""
    def __init__(self, detail):
        super().__init__(f"Tariff configuration error: {detail}")


class InvalidDateError(WaterBillingError):
    """Raised when a date field cannot be parsed."""
    def __init__(self, customer_id, date_str):
        self.customer_id = customer_id
        self.date_str = date_str
        super().__init__(
            f"Customer '{customer_id}' has an invalid payment due date: '{date_str}'."
        )
