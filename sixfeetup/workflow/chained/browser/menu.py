from plone.memoize.instance import memoize
from plone.app.contentmenu.menu import WorkflowSubMenuItem as BaseWorkflowSubMenuItem

class WorkflowSubMenuItem(BaseWorkflowSubMenuItem):
    """Overriding methods so WorkflowSubMenuItem can return a
       CSS-tagged list of workflows to display in Action items
    """
    
    def __init__(self, context, request):
        super(WorkflowSubMenuItem, self).__init__(context, request)
        self.workflows = self.tools.workflow().getWorkflowsFor(self.context)
    
    @memoize
    def available(self):
        """Need to determine if any workflows exist, and if so,
           the state names, as they may not include review_state
        """
        for w in self.workflows:
            state_var = w.variables.getStateVar()
            state = self.tools.workflow().getInfoFor(self.context, state_var, None)
            if state is not None:
                return True
        return False
    
    @memoize
    def _currentStateTitle(self):
        """Get the title of each workflow state to display in the
           workflow menu
        """
        wftool = self.tools.workflow()
        wftool_info = wftool.getInfoFor
        state_string = []
        if self.workflows:
            if len(self.workflows) == 1:
                state_var = self.workflows[0].variables.getStateVar()
                state = wftool_info(self.context, state_var, None)
                if self.workflows[0].states.has_key(state):
                    state_name = self.workflows[0].states[state].title or state
                return state_name
            else:
                for w in self.workflows:
                    state_var = w.variables.getStateVar()
                    state = wftool_info(self.context, state_var, None)
                    if w.states.has_key(state):
                        state_name = w.states[state].title or state
                        state_string.append("<span class='state-%s'>%s</span>" % (state, state_name))
                return ', '.join(state_string)
    
    @property
    def extra(self):
        if len(self.workflows) > 1:
            state = "chained"
        else:
            state = self.context_state.workflow_state()
        
        stateTitle = self._currentStateTitle()
        return {'id'         : 'plone-contentmenu-workflow',
                'class'      : 'state-%s' % state,
                'state'      : state,
                'stateTitle' : stateTitle,}
