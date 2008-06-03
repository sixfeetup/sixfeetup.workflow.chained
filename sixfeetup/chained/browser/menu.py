from plone.memoize.instance import memoize
from plone.app.contentmenu.menu import WorkflowSubMenuItem as BaseWorkflowSubMenuItem

class WorkflowSubMenuItem(BaseWorkflowSubMenuItem):

    @memoize
    def _currentStateTitle(self):
        """Get the title of each workflow state to display in the workflow 
        menu
        """
        wftool = self.tools.workflow()
        wftool_info = wftool.getInfoFor
        workflows = wftool.getWorkflowsFor(self.context)
        state_string = []
        if workflows:
            for w in workflows:
                state_var = w.variables.getStateVar()
                state = wftool_info(self.context, state_var, None)
                if w.states.has_key(state):
                    state_name = w.states[state].title or state
                    state_string.append(state_name)
        return ', '.join(state_string)
