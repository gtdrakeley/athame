import datetime

import buzz
import pendulum


class TestError(buzz.Buzz):
    pass


def frozen_time(moment=None):
    return pendulum.test(momentize(moment))


def momentize(moment):
    if moment is None:
        return pendulum.now("UTC")
    elif isinstance(moment, str):
        return pendulum.parse(moment, tz="UTC")
    elif isinstance(moment, datetime.datetime):
        return pendulum.instance(moment).in_tz("UTC")
    elif isinstance(moment, pendulum.DateTime):
        return moment.in_tz("UTC")
    else:
        raise TestError(f"Cannot create a moment from {moment}")


def moments_match(moment1, moment2):
    fixed_moment1 = momentize(moment1)
    fixed_moment2 = momentize(moment2)
    TestError.require_condition(
        fixed_moment1 == fixed_moment2,
        f"Moments do not match: {fixed_moment1} != {fixed_moment2}",
    )
    return True
