"""Application base class for displaying data.
"""
import abc
import logging

import pkg_resources

from .command import Command


LOG = logging.getLogger(__name__)


class DisplayCommandBase(Command):
    """Command base class for displaying data about a single object.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, app, app_args):
        super(DisplayCommandBase, self).__init__(app, app_args)
        self.load_formatter_plugins()

    @abc.abstractproperty
    def formatter_namespace(self):
        "String specifying the namespace to use for loading formatter plugins."

    @abc.abstractproperty
    def formatter_default(self):
        "String specifying the name of the default formatter."

    def load_formatter_plugins(self):
        self.formatters = {}
        for ep in pkg_resources.iter_entry_points(self.formatter_namespace):
            try:
                self.formatters[ep.name] = ep.load()()
            except Exception as err:
                LOG.error(err)
                if self.app_args.debug:
                    raise
        return

    def get_parser(self, prog_name):
        parser = super(DisplayCommandBase, self).get_parser(prog_name)
        formatter_group = parser.add_argument_group(
            title='output formatters',
            description='output formatter options',
            )
        formatter_choices = sorted(self.formatters.keys())
        formatter_default = self.formatter_default
        if formatter_default not in formatter_choices:
            formatter_default = formatter_choices[0]
        formatter_group.add_argument(
            '-f', '--format',
            dest='formatter',
            action='store',
            choices=formatter_choices,
            default=formatter_default,
            help='the output format to use, defaults to %s' % formatter_default,
            )
        for name, formatter in sorted(self.formatters.items()):
            formatter.add_argument_group(parser)
        return parser

    @abc.abstractmethod
    def get_data(self, parsed_args):
        """Return a two-part tuple with a tuple of column names
        and a tuple of values.
        """

    @abc.abstractmethod
    def run(self, parsed_args):
        column_names, data = self.get_data(parsed_args)
        formatter = self.formatters[parsed_args.formatter]
        formatter.emit_one(column_names, data, self.app.stdout, parsed_args)
        return 0
