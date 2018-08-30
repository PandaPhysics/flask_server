Backwards dynamo for T3 on-demand caching, with a backwards detox deletion agent.

Caching is done with PandaAnalysis (or other) jobs, and copying/access is communicated to this server via HTTP. 

Cronjob deletes old files once threshold is surpassed.  

This caching is implemented entirely on user space, so to limit duplication, one should perform a round-robin query of each user's cache.
For an example of this, look at the implementation of `PandaAnalysis.T3.request_data()`. 
