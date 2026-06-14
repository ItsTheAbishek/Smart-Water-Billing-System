# consumers.py
# Defines the WaterConsumer base class and all category-specific subclasses.

from abc import ABC, abstractmethod
from exceptions import InvalidCategoryError


class WaterConsumer(ABC):
    """
    Abstract base class representing a water consumer.

    All category-specific consumers must implement the compute_bill() method.
    """

    def __init__(self, customer_id: str, name: str, consumption_kl: float, tariff: dict):
        """
        Parameters
        ----------
        customer_id   : Unique customer identifier.
        name          : Customer name.
        consumption_kl: Water consumption in kilolitres.
        tariff        : Slab configuration dict for this category
                        (keys: 'slabs', 'fixed_charge').
        """
        self.customer_id   = customer_id
        self.name          = name
        self.consumption_kl = consumption_kl
        self.tariff        = tariff

    @abstractmethod
    def compute_bill(self) -> float:
        """
        Compute and return the total bill (before any late fee) for this consumer.
        Subclasses must implement slab-based pricing logic here.
        """
        pass

    def _apply_slabs(self) -> float:
        """
        Generic slab calculator shared by all subclasses.

        Iterates through the slab list and computes cumulative charges.
        Each slab covers (min → max) kilolitres at its given rate.
        The last slab (max == None) covers all remaining consumption.

        Returns
        -------
        float: Consumption charge (excluding fixed charge).
        """
        slabs = self.tariff["slabs"]
        remaining = self.consumption_kl
        charge = 0.0

        for slab in slabs:
            if remaining <= 0:
                break

            slab_min  = slab["min"]
            slab_max  = slab["max"]   # None means unbounded
            rate      = slab["rate"]

            # Units available in this slab
            if slab_max is None:
                units_in_slab = remaining
            else:
                slab_capacity = slab_max - slab_min + 1
                units_in_slab = min(remaining, slab_capacity)

            charge    += units_in_slab * rate
            remaining -= units_in_slab

        return charge

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"id={self.customer_id}, name={self.name}, "
            f"consumption={self.consumption_kl} kL)"
        )


# ── Derived Classes ────────────────────────────────────────────────────────────

class ResidentialConsumer(WaterConsumer):
    """
    Residential customer.
    Default slabs (from config):
        0–20 kL  → ₹20/kL
        21–50 kL → ₹35/kL
        >50 kL   → ₹50/kL
    Plus a fixed monthly charge.
    """

    def compute_bill(self) -> float:
        consumption_charge = self._apply_slabs()
        fixed              = self.tariff["fixed_charge"]
        return round(consumption_charge + fixed, 2)


class CommercialConsumer(WaterConsumer):
    """
    Commercial customer.
    Default slabs (from config):
        0–50 kL   → ₹50/kL
        51–150 kL → ₹75/kL
        >150 kL   → ₹100/kL
    Plus a fixed monthly charge.
    """

    def compute_bill(self) -> float:
        consumption_charge = self._apply_slabs()
        fixed              = self.tariff["fixed_charge"]
        return round(consumption_charge + fixed, 2)


class IndustrialConsumer(WaterConsumer):
    """
    Industrial customer.
    Default slabs (from config):
        0–100 kL  → ₹40/kL
        101–500 kL→ ₹65/kL
        >500 kL   → ₹90/kL
    Plus a fixed monthly charge.
    """

    def compute_bill(self) -> float:
        consumption_charge = self._apply_slabs()
        fixed              = self.tariff["fixed_charge"]
        return round(consumption_charge + fixed, 2)


# ── Factory Function ───────────────────────────────────────────────────────────

CATEGORY_MAP = {
    "Residential": ResidentialConsumer,
    "Commercial":  CommercialConsumer,
    "Industrial":  IndustrialConsumer,
}


def create_consumer(customer_id: str, name: str, category: str,
                    consumption_kl: float, tariff: dict) -> WaterConsumer:
    """
    Factory that returns the correct WaterConsumer subclass instance.

    Parameters
    ----------
    customer_id    : Unique customer identifier.
    name           : Customer name.
    category       : Customer category string (must exist in tariff config).
    consumption_kl : Consumption in kilolitres.
    tariff         : Full tariff dict (all categories) loaded by tariff_loader.

    Raises
    ------
    InvalidCategoryError : If the category is not in CATEGORY_MAP or the tariff dict.
    """
    if category not in CATEGORY_MAP or category not in tariff:
        raise InvalidCategoryError(category)

    cls             = CATEGORY_MAP[category]
    category_tariff = tariff[category]
    return cls(customer_id, name, consumption_kl, category_tariff)
