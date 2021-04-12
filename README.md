# Overview

This emulates a DC checker.

The real program would log into switches in a rack, identify attached server
management ports, log into the servers, check the connectivity
between servers and switches, and report this on a REST interface as JSON
objects.

This program reads a YAML description of a rack or racks and emulates what
an SDN controller might tell you about the devices concerned.

TODO: will report that servers are connected to TORs and other servers even
when those servers are not under management.  Given you couldn't put LLDP
on those servers without a management connection, that's unlikely to be
true in reality.

TODO: assumes the TORs don't use the management switch in the rack.  That
one is a 'maybe' - depends on the network engineer's preferences.

TODO: very little sunny-day testing, including none of the REST endpoints.
Should have tests to ensure that more than the valid.yaml test file actually
works.
