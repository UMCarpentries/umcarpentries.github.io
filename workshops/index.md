---
layout: index_page
category: workshops
title: Workshops
---

<div class="workshops">
	<ul>
	  {% for workshop in site.categories.workshops %}
			<li>
				<div class="meta">
					<div class="title">{{ workshop.title }}</div>
					<div><b>Dates:</b> {{ workshop.date | date: "%B %d" }} and {{ workshop.end_date | date: "%B %d, %Y" }}</div>
					<div><b>Instructors:</b> {{ workshop.instructors | join: ", "}}</div>
					<div><b>Helpers:</b> {{ workshop.helpers | join: ", "}}</div>
					<div><b>Content:</b> {{ workshop.material }}</div>
					<div><b>Audience:</b> {{ workshop.audience }}</div>
					<div><a href="{{workshop.site}}">More information</a></div>
				</div>
			</li>
	  {% endfor %}
	</ul>
</div>
