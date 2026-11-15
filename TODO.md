# To do

- [ ] **Archive page size.** `collect.py` and `graph.py` ask the archive for `limit=100` posts per request.
      Check what the archive returns when no limit is set, and whether its own default (or an automatic
      setting, if it has one) is faster or safer. If it is, drop the fixed limit and let the archive decide.
