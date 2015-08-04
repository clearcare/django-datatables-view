# -*- coding: utf-8 -*-
from .mixins import JSONResponseView


class BaseDatatableView(JSONResponseView):
    """ JSON data for datatables
    """
    order_columns = []
    max_display_length = 100  # max limit of records returned, do not allow to kill our server by huge sets of data

    def initialize(*args, **kwargs):
        pass

    def get_order_columns(self):
        """ Return list of columns used for ordering
        """
        return self.order_columns

    @staticmethod
    def build_order_by(request, order_columns):
        # Number of columns that are used in sorting
        try:
            i_sorting_cols = int(request.REQUEST.get('iSortingCols', 0))
        except ValueError:
            i_sorting_cols = 0

        order = []
        for i in range(i_sorting_cols):
            # sorting column
            try:
                i_sort_col = int(request.REQUEST.get('iSortCol_%s' % i))
            except ValueError:
                i_sort_col = 0
            # sorting order
            s_sort_dir = request.REQUEST.get('sSortDir_%s' % i)

            sdir = '-' if s_sort_dir == 'desc' else ''

            try:
                sortcol = order_columns[i_sort_col]
            except IndexError:
                continue
            if isinstance(sortcol, list):
                for sc in sortcol:
                    order.append((sdir, sc))
            else:
                order.append((sdir, sortcol))
        return order

    def ordering(self, qs):
        """ Get parameters from the request and prepare order by clause
        """
        order = self.build_order_by(self.request, self.get_order_columns())
        if order:
            return qs.order_by(*[''.join(order_by) for order_by in order])
        return qs

    @staticmethod
    def build_paging(request, max_length):
        limit = min(int(request.REQUEST.get('iDisplayLength', 10)), max_length)
        # if pagination is disabled ("bPaginate": false)
        if limit == -1:
            return qs
        start = int(request.REQUEST.get('iDisplayStart', 0))
        offset = start + limit
        return start, offset

    def paging(self, qs):
        """ Paging
        """
        start, offset = self.build_paging(self.request, self.max_display_length)
        return qs[start:offset]

    # TO BE OVERRIDEN
    def get_initial_queryset(self):
        raise Exception("Method get_initial_queryset not defined!")

    def filter_queryset(self, qs):
        return qs

    def prepare_results(self, qs):
        return []
    # /TO BE OVERRIDEN

    def get_context_data(self, *args, **kwargs):
        request = self.request
        self.initialize(*args, **kwargs)

        qs = self.get_initial_queryset()

        # number of records before filtering
        total_records = qs.count()

        qs = self.filter_queryset(qs)

        # number of records after filtering
        total_display_records = qs.count()

        qs = self.ordering(qs)
        qs = self.paging(qs)

        # prepare output data
        aaData = self.prepare_results(qs)

        ret = {'sEcho': int(request.REQUEST.get('sEcho', 0)),
               'iTotalRecords': total_records,
               'iTotalDisplayRecords': total_display_records,
               'aaData': aaData
               }

        return ret
