---
layout: index_page
category: instructors
title: Instructors
---

The Software and Data Carpentry instructors at the University of Michigan represent a diverse array of backgrounds, interests, and goals.

{% assign page_array = site.instructors | where:"status", "current"	%}
{% include picture_grid.html pages=page_array columns=4	%}


<h3>Alumni</h3>
<p>While we hate to say goodbye, our goal is to train people and then send them on to spread the mission of the Carpentries</p>

{% assign page_array = site.instructors | where:"status","alumni"		%}
{% include picture_grid.html pages=page_array columns=4				%}
