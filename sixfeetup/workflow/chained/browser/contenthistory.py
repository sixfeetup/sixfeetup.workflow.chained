import logging

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import log

from plone.app.layout.viewlets.content import ContentHistoryView as ContentHistoryViewBase


class ContentHistoryView(ContentHistoryViewBase):

    def workflowHistory(self, complete=True):
        """Return workflow history of this context, for all workflows in its
        chain.

        Taken from plone_scripts/getWorkflowHistory.py
        """
        context = aq_inner(self.context)
        # Since switching to DCWorkflow's getInfoFor, we rely on its
        # permission checks.
        #if not (_checkPermission('Request review', context) or
        #    _checkPermission('Review portal content', context)):
        #    return []

        wf_tool = getToolByName(context, 'portal_workflow')
        membership = getToolByName(context, 'portal_membership')
        workflows = wf_tool.getWorkflowsFor(self.context)

        review_history = []

        try:
            # get total history
            for wf in workflows:
                wf_review_history = wf.getInfoFor(context,
                                                  'review_history', [])
                # Add in the state_var, to find the title and use in template
                for item in wf_review_history:
                    item['state_var'] = wf.state_var
                review_history.extend(wf_review_history)

            if not complete:
                # filter out automatic transitions.
                review_history = [r for r in review_history if r['action']]
            else:
                review_history = list(review_history)

            portal_type = context.portal_type
            anon = _(u'label_anonymous_user', default=u'Anonymous User')

            for r in review_history:
                r['type'] = 'workflow'
                r['transition_title'] = wf_tool.getTitleForTransitionOnType(
                    r['action'], portal_type) or _("Create")
                r['state_title'] = wf_tool.getTitleForStateOnType(
                    r[r['state_var']], portal_type)
                actorid = r['actor']
                r['actorid'] = actorid
                if actorid is None:
                    # action performed by an anonymous user
                    r['actor'] = {'username': anon, 'fullname': anon}
                    r['actor_home'] = ''
                else:
                    r['actor'] = membership.getMemberInfo(actorid)
                    if r['actor'] is not None:
                        r['actor_home'] = self.navigation_root_url + '/author/' + actorid
                    else:
                        # member info is not available
                        # the user was probably deleted
                        r['actor_home'] = ''
            review_history.reverse()

        except WorkflowException:
            log('plone.app.layout.viewlets.content: '
                '%s has no associated workflow' % context.absolute_url(),
                severity=logging.DEBUG)

        return review_history
