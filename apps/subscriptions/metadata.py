import attr
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from djstripe.enums import PlanInterval
from djstripe.models import Product, Plan

from .exceptions import SubscriptionConfigError
from .serializers import PlanSerializer, ProductSerializer


@attr.s
class ProductMetadata(object):
    """
    Metadata for a Stripe product.
    """
    stripe_id = attr.ib()
    name = attr.ib()
    features = attr.ib(type=list)
    description = attr.ib(default='')
    is_default = attr.ib(type=bool, default=False)

    @classmethod
    def from_stripe_product(cls, stripe_product, **kwargs):
        defaults = dict(
            stripe_id=stripe_product.id,
            name=stripe_product.name,
            features=[]
        )
        defaults.update(kwargs)
        return cls(
            **defaults
        )


@attr.s
class ProductWithMetadata(object):
    """
    Connects a Stripe product to its ProductMetadata.
    """
    product = attr.ib()
    metadata = attr.ib()


    @property
    def stripe_id(self):
        return self.metadata.stripe_id or self.product.id

    @cached_property
    def default_plan(self):
        if not ACTIVE_PLAN_INTERVALS:
            raise SubscriptionConfigError(_('At least one plan interval (year or month) must be set!'))
        return self.monthly_plan if ACTIVE_PLAN_INTERVALS[0] == PlanInterval.month else self.annual_plan

    @cached_property
    def annual_plan(self):
        return self._get_plan(PlanInterval.year)

    @cached_property
    def monthly_plan(self):
        return self._get_plan(PlanInterval.month)

    def _get_plan(self, interval):
        if self.product:
            try:
                return self.product.plan_set.get(interval=interval, interval_count=1)
            except (Plan.DoesNotExist, Plan.MultipleObjectsReturned):
                raise SubscriptionConfigError(_(
                    f'Unable to select a "{interval}" plan for {self.product}. '
                    'Have you setup your Stripe objects and run ./manage.py djstripe_sync_plans_from_stripe? '
                    'You can also hide this plan interval by removing it from ACTIVE_PLAN_INTERVALS in '
                    'apps/subscriptions/metadata.py'
                ))

    def to_dict(self):
        """
        :return: a JSON-serializable dictionary for this object,
        usable in an API.
        """
        def _serialized_plan_or_none(plan):
            return PlanSerializer(plan).data if plan else None

        return {
            'product': ProductSerializer(self.product).data,
            'metadata': attr.asdict(self.metadata),
            'default_plan': _serialized_plan_or_none(self.default_plan),
            'annual_plan': _serialized_plan_or_none(self.annual_plan),
            'monthly_plan': _serialized_plan_or_none(self.monthly_plan),
        }


@attr.s
class PlanIntervalMetadata(object):
    """
    Metadata for a Stripe product.
    """
    interval = attr.ib()
    name = attr.ib()



def get_plan_name_for_interval(interval):
    return {
        PlanInterval.year: _('Annual'),
        PlanInterval.month: _('Monthly'),
    }.get(interval, _('Custom'))


def get_active_plan_interval_metadata():
    return [
        PlanIntervalMetadata(interval=interval, name=get_plan_name_for_interval(interval))
        for interval in ACTIVE_PLAN_INTERVALS
    ]

# Active plan intervals. Only allowed values are "PlanInterval.month" and "PlanInterval.year"
# Remove one of them to only allow monthly/annual pricing.
# The first element is considered the default
ACTIVE_PLAN_INTERVALS = [
    PlanInterval.year,
    PlanInterval.month,
]


# These are the products that will be shown to users in the UI and allowed to be associated
# with plans on your side
ACTIVE_PRODUCTS = [
    ProductMetadata(
        stripe_id='',
        name=_('Starter'),
        description=_('For hobbyists and side-projects'),
        features=[
            _('Up to 100 Widgets'),
            _('Unlimited Widget Editing'),
        ],
    ),
    ProductMetadata(
        stripe_id='',
        name=_('Standard'),
        description=_('For small businesses and teams'),
        is_default=True,
        features=[
            _('Up to 500 Widgets'),
            _('Unlimited Widget Editing'),
            _('Advanced Widget Editing Features'),
        ],
    ),
    ProductMetadata(
        stripe_id='',
        name=_('Premium'),
        description=_('For small businesses and teams'),
        features=[
            _('Unlimited Widgets'),
            _('All Features'),
            _('Priority Support and Training'),
        ],
    ),
]

ACTIVE_PRODUCTS_BY_ID = {
    p.stripe_id: p for p in ACTIVE_PRODUCTS
}


def get_active_products_with_metadata():
    # if we have set active products in metadata then filter the full list
    if ACTIVE_PRODUCTS:
        for product_meta in ACTIVE_PRODUCTS:
            try:
                yield ProductWithMetadata(
                    product=Product.objects.get(id=product_meta.stripe_id),
                    metadata=product_meta,
                )
            except Product.DoesNotExist:
                raise SubscriptionConfigError(_(
                    f'No Product with ID "{product_meta.stripe_id}" found! '
                    f'This is coming from the "{product_meta.name}" Product in the ACTIVE_PRODUCTS variable '
                    f'in metadata.py. '
                    f'Please make sure that all products in ACTIVE_PRODUCTS have a valid stripe_id and that '
                    f'you have synced your Product database with Stripe.'
                ))
    else:
        # otherwise just use whatever is in the DB
        for product in Product.objects.all():
            yield ProductWithMetadata(
                product=product,
                metadata=ACTIVE_PRODUCTS_BY_ID.get(product.id, ProductMetadata.from_stripe_product(product))
            )
        else:
            raise SubscriptionConfigError(_(
                'It looks like you do not have any Products in your database. '
                'In order to use subscriptions you first have to setup Stripe billing and sync it '
                'with your local data.'
            ))


def get_product_with_metadata(djstripe_product):
    if djstripe_product.id in ACTIVE_PRODUCTS_BY_ID:
        return ProductWithMetadata(
            product=djstripe_product,
            metadata=ACTIVE_PRODUCTS_BY_ID[djstripe_product.id]
        )
    else:
        return ProductWithMetadata(
            product=djstripe_product,
            metadata=ProductMetadata.from_stripe_product(djstripe_product)
        )

def get_product_and_metadata_for_subscription(subscription):
    if not subscription:
        return None
    return get_product_with_metadata(subscription.plan.product)
