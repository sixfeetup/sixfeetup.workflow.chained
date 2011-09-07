import urllib
import pkg_resources
from zope.component import getMultiAdapter
from zope.app.pagetemplate import ViewPageTemplateFile
from plone.app.content.browser.foldercontents \
    import FolderContentsView as BaseFolderContentsView
from plone.app.content.browser.foldercontents \
    import FolderContentsTable as BaseFolderContentsTable
from plone.app.content.browser.tableview import Table as BaseTable
from plone.memoize import instance
from Products.ATContentTypes.interface import IATTopic
from Products.CMFCore.utils import getToolByName


class Table(BaseTable):
    """
    """
    render = ViewPageTemplateFile("table.pt")
    batching_template = pkg_resources.resource_filename(
                            'plone.app.content.browser',
                            'batching.pt')
    batching = ViewPageTemplateFile(batching_template)


class FolderContentsView(BaseFolderContentsView):
    """
    """

    def contents_table(self):
        table = FolderContentsTable(self.context, self.request)
        return table.render()


class FolderContentsTable(BaseFolderContentsTable):
    """
    The foldercontents table renders the table and its actions.
    """

    def __init__(self, context, request, contentFilter={}):
        self.context = context
        self.request = request
        self.contentFilter = contentFilter
        url = self.context.absolute_url()
        view_url = url + '/@@folder_contents'
        self.table = Table(request, url, view_url, self.items,
                           show_sort_column=self.show_sort_column,
                           buttons=self.buttons)

    @property
    @instance.memoize
    def items(self):
        """
            We override state_class and state_title
            when returning values for multi-state content.
        """
        context = self.context
        request = self.request
        self.context_state = getMultiAdapter((context, request),
            name='plone_context_state')
        self.tools = getMultiAdapter((context, request), name='plone_tools')
        self.workflows = self.tools.workflow().getWorkflowsFor(self.context)
        plone_utils = getToolByName(self.context, 'plone_utils')
        plone_view = getMultiAdapter(
            (self.context, self.request), name=u'plone')
        portal_properties = getToolByName(self.context, 'portal_properties')
        site_properties = portal_properties.site_properties
        use_view_action = site_properties.getProperty(
            'typesUseViewActionInListings', ())
        browser_default = self.context.browserDefault()

        if IATTopic.providedBy(self.context):
            contentsMethod = self.context.queryCatalog
        else:
            contentsMethod = self.context.getFolderContents

        results = []
        for i, obj in enumerate(contentsMethod(self.contentFilter)):
            if (i + 1) % 2 == 0:
                table_row_class = "draggable even"
            else:
                table_row_class = "draggable odd"

            url = obj.getURL()
            path = obj.getPath or "/".join(obj.getPhysicalPath())
            icon = plone_view.getIcon(obj);

            type_class = 'contenttype-' + plone_utils.normalizeString(
                obj.portal_type)

            review_state = obj.review_state
            state_class = 'state-' + plone_utils.normalizeString(review_state)

            relative_url = obj.getURL(relative=True)
            obj_type = obj.portal_type

            modified = plone_view.toLocalizedTime(
                obj.ModificationDate, long_format=1)

            if obj_type in use_view_action:
                view_url = url + '/view'
            elif obj.is_folderish:
                view_url = url + "/folder_contents"
            else:
                view_url = url

            is_browser_default = len(browser_default[1]) == 1 and (
                obj.id == browser_default[1][0])

            # XXX: This does not get the proper workflow chain when we
            #      are dealing with an item that is under placeful
            #      workflow control.
            state_list = []
            wf_chain = self.tools.workflow().getChainForPortalType(obj_type)
            for w in wf_chain:
                wf_obj = self.tools.workflow()[w]
                state_var = wf_obj.state_var
                state_id = getattr(obj, state_var, None)
                wf_states = wf_obj.states
                # XXX: This is a bit of a hack, if there is a placeful
                #      worklflow in use then this might still be wrong.
                #      Since the state id could be the same in different
                #      workflows. The title it ends up getting might
                #      not be the correct one.
                if state_id is None or state_id not in wf_states.objectIds():
                    continue
                stitle = wf_states[state_id].title
                state_list.append('<span class="wf-%s state-%s">%s</span>'
                    % (w, state_id, stitle))
            # XXX: If the state didn't exist in the workflow chain,
            #      fall back to the `review_state` on the brain. This
            #      Will happen when a placeful workflow is in place
            #      and the workflow chain cannot be determined.
            if not state_list and isinstance(review_state, basestring):
                state_list = [review_state]
            state_string = ', '.join(state_list)

            results.append(dict(
                url = url,
                id  = obj.getId,
                quoted_id = urllib.quote_plus(obj.getId),
                path = path,
                title_or_id = obj.pretty_title_or_id(),
                description = obj.Description,
                obj_type = obj_type,
                size = obj.getObjSize,
                modified = modified,
                icon = icon.html_tag(),
                type_class = type_class,
                wf_state = review_state,
                state_title = state_string,
                state_class = state_class,
                is_browser_default = is_browser_default,
                folderish = obj.is_folderish,
                relative_url = relative_url,
                view_url = view_url,
                table_row_class = table_row_class,
                is_expired = self.context.isExpired(obj),
            ))
        return results
