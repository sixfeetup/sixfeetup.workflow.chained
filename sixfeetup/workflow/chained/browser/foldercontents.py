from zope.component import getMultiAdapter
from Products.ATContentTypes.interface import IATTopic
from Products.CMFCore.utils import getToolByName

#from plone.memoize.instance import memoize

from plone.app.content.browser.foldercontents \
    import FolderContentsView as BaseFolderContentsView
from plone.app.content.browser.foldercontents \
    import FolderContentsTable as BaseFolderContentsTable

from plone.memoize import instance

import urllib


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
    
    def __init__(self, context, request):
        super(FolderContentsTable, self).__init__(context, request)
    
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
            
            state_list = []
            wf_chain = self.tools.workflow().getChainForPortalType(obj_type)
            for w in wf_chain:
                wf_obj = self.tools.workflow()[w]
                state_var = wf_obj.state_var
                state_id = getattr(obj, state_var, None)
                if state_id is not None:
                    stitle = wf_obj.states[state_id].title
                    state_list.append('<span class="wf-%s state-%s">%s</span>'
                        % (w, state_id, stitle))
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
