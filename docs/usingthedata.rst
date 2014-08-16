Using the lobbying data
=========================

Who must report lobbying data?
------------

- Organizations that employ lobbyists must report on what lobbyists they employ and their activity
- Lobbyists must report on their activity and who they are employed by
- Legislators and state agencies must report on what gifts they receive from lobbyists

What kind of activity is reported?
------------

** Lobbyist employers **
Entities that employ lobbyists include corporations, nonprofit organizations and local governments. They file registration reports 

** Lobbyists **


** Government agencies and officials **

Some queries you might want to run
--------------
Gifts: Who gave the most in gifts to legislators

gift_totals = Gift.objects.filter(date__gte='2000-01-01').values('filing__filer__pk','filing__filer__name').annotate(Sum('payment_amount')).order_by('-payment_amount__sum')

Gifts: Who received the most in gifts to legislators?
Gift.objects.filter(date__gte='2000-01-01').values('recipient').annotate(Sum('payment_amount')).order_by('-payment_amount__sum')


Campaign contributions from lobbyists: Who received the most in contributions from lobbyists?
biggest_receivers = Contribution.objects.filter(ctrib_date__gte='2000-01-01').values('recipient').annotate(Sum('amount')).order_by('-amount__sum')


Gotchas and caveats
-----------
- The recipient fields are reliant on whatever the lobbyists wrote for a recipient name, so variations will be difficult to group by. For example: John Smith, John M. Smith and Jonathan Smith are all possible entries in the recipient field that may (or may not) be the same person. There are ways to rewrite this query as case-insensitive, but the example query is case sensitive. This means that John Smith and JOHN SMITH would not be grouped together.

-The gift recipient field also sometimes is filled out as something like "See Attachment A", which may indicate that the lobbyist reported multiple people as recipients of a given gift.

- Do lobbyists need to refile every session? year? x years? If so there may be more than one registration for each lobbyist in the database

- When searching for bills in the description of lobbying activity, remember that bill numbers start over with every session, so you must make sure to search for activity during the approrpriate session.

- All of lobbying is a work in progress, but the Report model especially is not ironed out. It's very likely that we're currently importing multiple instances of the same report that has been amended several times.