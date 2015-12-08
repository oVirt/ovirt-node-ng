
# oVirt Engine Integration


The primary consumer of oVirt Node is oVirt Engine.
Several aspects of this integration are discussed in this section.

## Overview

**FIXME**

- No updates through Engine
- Host discovers updates itself, then signals that an upgrade is available
  to Engine. Needs RFE
- RFE needed to let Engine rollback host if needed
  (chain: engine->vdsm->imgbase)
