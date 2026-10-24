<!-- SPDX-FileCopyrightText: 2026 Shaan Narendran <shaannaren06@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Agentic Resource Discovery: speaker script

About 25 minutes at a relaxed pace, plus Q&A. Cues in [brackets] tell you where to point or pause.

## 1. Title · 0:30

Hi everyone, I'm Shaan, and today I want to talk about Agentic Resource Discovery, or ARD.

[Point to the search card] This is the whole idea in one picture. You type what you need, "find me a flight booking agent", and you get back ranked resources: an A2A agent, an MCP server, a skill, each with a relevance score.

The interesting part is that the agent had none of these installed beforehand. It found them.

## 2. Agenda · 0:45

A quick intro: I'm an open-source contributor, and over the last couple of months I implemented ARD in Observal, an open-source registry and observability platform for AI coding agents. So this talk is half spec, half field notes.

Five parts: why agents need discovery at all, what ARD actually specifies, how I implemented it and what I learned, what it unlocks, and how you can try it on your own project this week.

## 3. Agents only use what someone wired up in advance · 1:00

Quick show of hands: how many of you have more than five MCP servers configured right now? More than twenty? [Pause]

Today an agent can only use what someone wired up in advance: the MCP servers in its config, the skills in its folder. [Point to the orange squares] That's these three.

But there are thousands of MCP servers, A2A agents and skills out there, including inside your own company. All these grey squares. The agent can't see them, so it either rebuilds something that already exists or tells you it can't help.

The capability was there. It just wasn't findable.

## 4. Loading every tool into the prompt doesn't scale · 1:00

The obvious fix is to connect everything. That breaks fast.

[Left box] This box is the model's context window. The orange row is your task: book a flight to Tokyo. Every purple row is a tool description: GitHub, Slack, Jira, Postgres, and thousands more. Most agents put every connected tool's description in here, on every turn. With five tools that's fine. With five thousand, the window is full before your task gets a look in: it burns tokens, slows things down, and the model chooses worse.

[Right side] ARD moves the choosing out of the model. Your task goes to a search service that indexes thousands of resources, and only the top three matches come back into the context: a travel agent, a flight-status server, a trip-planning skill. [Point to the dashed box] Everything else stays free for the actual work.

It's the same shift the web went through, which brings me to this quote.

## 5. "Search engines lit the web up." · 0:30

That's R.V. Guha, introducing ARD in June. Guha helped create RSS and schema.org, so he's seen this pattern before.

Early on, the web lived in hand-curated directories, and search engines made it usable. Agentic resources are in that directory era right now: curated lists, marketplaces, config files. ARD is a search layer for them.

## 6. ARD is an open spec · 1:00

So what is ARD, concretely? It's an open specification, announced on 17 June this year. The current version is 0.91, still marked as a Proposal, and it's Apache-licensed.

The authors are Junjie Bu from Google, R.V. Guha, and Shaun Smith from Hugging Face. [Gesture to the chips] It's developed with a long list of companies: Cisco, Databricks, GitHub, Google, Microsoft, Nvidia, Salesforce and more.

It's not just a document. There are already two reference implementations: GitHub's agent finder, which lets Copilot discover tools at runtime, and Hugging Face's Discover Tool.

And it's open on GitHub. Spec changes start as issues, so anyone in this room can take part.

## 7. ARD runs before invocation · 1:00

Where does ARD fit? Before invocation.

[Top] The agent asks: what exists for this task? [Middle] ARD answers that: it describes, publishes, searches and federates. [Bottom] Then the agent calls the chosen resource through that resource's own protocol: MCP for an MCP server, A2A for an agent, and so on.

So ARD doesn't replace MCP, A2A or Skills. It's an envelope around them. [Right] The spec is explicit about what it leaves to others: authentication belongs to the resource's protocol, distribution to OCI or npm, invocation to MCP or A2A.

For this community, a simple way to put it: MCP is how agents talk to tools; ARD is how they find them.

## 8. One small JSON-LD entry · 1:15

The basic unit is the entry: one small JSON-LD document per resource. This one comes straight from the spec, a weather MCP server.

[Coral keys] Four fields are required: an identifier, a display name, a type, which is a media type like mcp-server-card+json, and a url pointing at the artifact. Or you can put the artifact inline as data.

[Violet key] The one I want you to remember is representativeQueries: two to five plain-language requests this resource can handle. That's what search indexes. It's only a SHOULD, but leave it out and your entry is valid and nobody finds it.

[Grey keys] Everything else is optional. And because it's JSON-LD, you can add your own vocabulary through @context, and those terms become filters without anyone changing the spec.

## 9. The identifier names the resource · 1:15

Every entry has an identifier that starts with urn:air.

[Walk the chips left to right] "urn" says this is a name, not an address. "air" is ARD's namespace. Early drafts used urn:ai, but URN rules need more than two characters, so it became air. Then comes the publisher, which must be a real domain, an optional namespace, and the resource name.

Why not just use the URL as the ID? Because a URL answers "where is it right now?", and an identifier needs to answer "what is it, and who stands behind it?" Three reasons.

[Card 1] Stable. Think of a person's name versus their home address. If Acme moves its weather server to a new host, a URL-based ID would break every registry and every saved config. With a URN, the name stays the same and only the url field changes.

[Card 2] Verifiable. Anyone can publish a JSON file claiming to be Google's official Gmail agent. ARD ties the name to a domain: an entry named urn:air:google.com-anything must carry proof issued by google.com in its trust manifest. Same idea as HTTPS: you only get a certificate for google.com if you control google.com. No proof, and a registry that checks rejects it.

[Card 3] Unique without a referee. When registries merge results, two publishers will both call something "weather". Instead of a central body handing out names, ARD reuses DNS: only one organisation owns acme.com, so everything under urn:air:acme.com is theirs. If you've written Java, it's the same trick as com.acme package names.

## 10. Five ways to publish · 1:00

How do registries find your entry? There's a static layer that works a lot like publishing web pages.

There are five mechanisms. [Top two rows] These two are the ones consumers must check: a manifest at /.well-known/ard.json, which is just JSON with an entries array, and a link tag with rel="ard" in your HTML.

[Other rows] You can also embed the entry as JSON-LD on the resource's own page, add an Agentmap line to robots.txt, or publish DNS records that point at your entries or at a search endpoint.

One tip: older articles mention ai-catalog.json. That's the predecessor. Publish ard.json.

## 11. Registries and one REST search API · 1:00

The dynamic layer is registries.

[Top flow] Publishers put entries out. Registries ingest them: web crawling is required, and scanning git, npm or OCI is optional. They build an index, and clients query it.

[Endpoints] The key rule is that every registry exposes the same REST API, so a client written once works against any registry. POST /search is mandatory. Explore gives facet counts, List gives deterministic browsing, and a registry can also wrap search as an MCP tool or an A2A skill.

[Code] A request is simple: some text, optional filters (here, only A2A agents), a federation mode and a page size. Federation is next.

## 12. Federation: three modes · 1:00

With many registries around, a natural question is: does my search only see one of them? Federation answers that. A registry is itself an ARD entry, so registries can find each other like any other resource. And because they all speak the same search API, one registry can simply ask another over HTTP.

The client chooses how far a search goes, with one field in the request. [Card 1] auto, the default: the registry asks other registries on your behalf and merges everything into one list. [Card 2] referrals: the registry gives you its own answers plus "you could also try these registries", and you decide. [Card 3] none: only this registry's own index; your query goes nowhere else.

[Bottom] If you know DNS: auto is like a resolver that does the whole lookup for you; referrals is a server saying "I don't know, but ask them."

## 13. Federation, step by step · 1:15

Here's the spec's own example. Read it top to bottom. [Top] The user asks: book me a flight to Tokyo and file the travel expense report.

[Step 1] The orchestrator, which is the user's agent, searches the company's internal registry in referrals mode.

[Step 2] The company registry answers: here's our internal expenses agent, a strong match at 97, and here are two other registries you could try for the rest.

[Step 3] The orchestrator picks the travel finder and asks it only about the flight. Notice what it doesn't send: anything about the expense report. That stays inside the company. That's the point of referrals: the agent decides where each part of its question goes.

[Step 4] The travel finder returns a flight booking agent.

[Step 5] Now the orchestrator has both agents and calls each one through its own protocol. ARD's job ended at step 4: it finds things; it doesn't run them.

## 14. Relevance and trust are kept apart · 1:00

One design choice I really like is that relevance and trust are kept apart.

[Left] The score, 0 to 100, means only how well an entry matches your request. The spec says in capital letters that it MUST NOT be read as a trust, compliance or safety rating.

[Right] Trust lives in the trust manifest. ARD requires one thing of it: the identity must match the publisher domain in the URN. On top of that it can carry attestations, such as SOC 2 audits, security scans or build provenance, under whatever framework you use: SPIFFE, DIDs, your company PKI. Registries verify it and can filter on it.

Why it matters: a top-ranked result should never look trustworthy just because it ranked first.

That's the spec. Now let me show you what it took to implement it.

## 15. Observal had a registry · 1:00

Observal is an open-source registry and observability platform for AI coding agents. An agent there bundles MCP servers, skills, hooks, prompts and sandboxes. The model was install-first: build an agent, get it approved, pull it into Claude Code or Cursor or Kiro, then start working.

[Orange icon] That has exactly the gap from earlier: mid-task, the assistant can't see approved resources it wasn't given.

ARD fit cleanly because it deliberately doesn't do installation, review or telemetry, and Observal already had all three. [Card] So the principle I wrote into the project's first ADR was: ARD says what exists; Observal says how to use it safely.

[Numbers] The pull request came to 23 commits and 90 files, about ten thousand lines, more than four thousand of them tests.

## 16. A projection, not a rewrite · 1:00

The most important decision was that I didn't touch the existing tables.

[Left] Agents, MCP servers, skills and the rest stay the source of truth for install, review and ownership.

[Middle] One adapter per kind turns each approved version into a neutral entry and writes it to a new read model called discovery_entries. The adapters also derive representative queries from metadata, flagged as derived so they're never passed off as the publisher's own words.

[Right] Everything ARD-facing reads from that table: the manifest, search, versioned artifacts with digests, and Observal's CLI, web page and agent skill.

Keeping it fresh is one idempotent function, triggered after every change, by a safety-net job four times a day, and on first boot. No existing API changed.

## 17. Six endpoints · 0:45

Every resource got one permanent URN. [Chips] Two details here. I used the internal UUID, not the readable name, because names change on rename or transfer and a URN mustn't. And the publisher domain is pinned once, so identifiers don't change if the deployment moves.

[Table] Four endpoints come from the spec: the manifest, search, list, and explore, which honestly returns 501 until facets ship. Two are mine: fetching one full entry by URN, because the spec has no operation for that, and permanent artifact URLs that always return the exact same bytes for a version, with a digest.

## 18. Postgres narrows, Python ranks, CI checks · 1:00

For search, I avoided new infrastructure. [Step 1] Postgres narrows: visibility rules, filters and a trigram-indexed text match, giving at most five thousand candidates. [Step 2] Python ranks: each query word is scored against the name, the representative queries, the capabilities and the description, in that order of weight. [Step 3] And every result explains itself with the words that matched.

[Chart] I didn't want to guess whether that's good enough, so there's a benchmark in CI: 47 requests written the way developers actually ask. Recall at 5 is 0.96 for the ranker and 0.94 end to end. The grey bars are floors: drop below them and the build fails, and the rule is that floors only go up.

The misses are synonyms, like "PRs" versus "pull requests". That's where semantic search would come in next.

## 19. Guardrails · 1:00

Discovery could easily become a back door around a registry's rules, so I built in four guardrails.

[Top left] Score means relevance only, as the spec says. Approval and harness support are separate fields, and policy filters run before ranking.

[Top right] Discovery never shows more than the registry already would. Drafts and rejected items only reach their owners.

[Bottom left] Search text stays home. People type sensitive things into search, such as incident details or unreleased product names, so federation only reaches upstreams an admin allowlists, and that list starts empty.

[Bottom right] Read freely, write with consent. Approved text loads straight away; anything that changes your setup asks first.

## 20. What I learned · 1:15

Five lessons from implementing a spec that was still moving.

One: pin it. I vendored the schemas and the official conformance tool at one commit and run them in CI, so updating the spec is a reviewed change, not a surprise.

Two: write decisions down. An ADR with ten decisions meant reviewers debated choices, not code.

Three: project, don't rewrite. Nothing existing broke.

Four: the spec changed while I was building. The well-known path, the URN prefix and the MCP media type all got new names. So accept the old spellings on input and always emit the new ones.

Five: be honest about conformance. The spec says registries must crawl, and I haven't built crawling yet, so Observal is a publisher and search endpoint, not a full registry, and the docs say so.

## 21. Agents search before they reinvent · 1:00

So what does this unlock? The first use case is the one that started all of this: agents search before they reinvent.

[Terminal] Observal ships an agent skill to every coding harness it supports. I rewrote it so that at the start of real work, such as a review, writing tests or querying a database, the assistant searches first. It gets ranked candidates with the matching words, can inspect the best one, then use it. For a skill, the exact approved version is loaded straight into the session, and the use is recorded.

[Note] The output here is simplified and the resource names are examples. An empty result is a valid answer: the agent retries once with different words, then gets on with the job.

## 22. Text loads now; setup changes ask first · 0:45

What happens on "use" depends on what the resource touches. This is where Observal's governance does the work ARD leaves out.

[Orange] Skills and prompts are just text, so they load now. [Violet] MCP servers, agents and sandboxes change your configuration, so nothing is written automatically. You get the normal install command, which asks first and applies after a restart. [Lilac] Hooks are never activated implicitly.

[Bottom] And unapproved resources, or ones your harness doesn't support, are refused unless you explicitly override.

## 23. Every use is recorded · 1:00

Because every use goes through one place, we know what a session actually relied on.

[Walk left to right] Each use writes one local line: which resource, its exact version and digest, which harness, which folder, and when. When the session's telemetry is uploaded, those uses are attached to it. So the dashboard shows which approved resources a session used, with no new tracking.

[Command] Then the loop closes. If a combination worked, say a security skill, a checklist and the GitHub MCP server, this command turns it into a draft agent pinned to those exact versions. Ad-hoc discovery becomes a reviewed, reusable asset for the next person.

## 24. Findable everywhere · 1:00

Zooming out from Observal, here's what ARD enables for everyone.

[Card 1] If you build an MCP server, skill or agent, you publish one ard.json and any ARD registry can find you. No separate submission to every marketplace.

[Card 2] Companies can run an internal registry that answers with approved resources first and refers out to public ones for the rest. That's the federation example from earlier.

[Card 3] Coding agents can find tools at runtime instead of at config time. GitHub and Hugging Face already do it.

[Card 4] And governed catalogues like the one I built can add approval and telemetry on top while still speaking the open standard. Open ecosystems, not walled catalogues.

## 25. Try it this week · 1:00

If you take one thing home: you can publish an ARD entry for your own project this week. It's one small file.

[Code] Step one: put an ard.json under /.well-known on your domain. Here's a made-up Chennai weather MCP server. It has the four required fields, and please write good representative queries, because that's what search runs on.

[Top right] Step two: validate it with the official conformance tool from the ard-spec repo. Publisher mode fetches your file and checks it.

[Bottom right] Step three: join in. The spec is at version 0.91, so feedback now actually shapes it. Issues for spec changes; pull requests welcome for examples, tools and implementations.

## 26. Thank you · Q&A

To wrap up: agents shouldn't be limited to what someone wired up in advance. ARD gives them a search layer: a small entry, a permanent domain-anchored name, one REST API, federation across registries, and trust kept separate from relevance. And I've shown you what it took to build that into a real open-source registry.

Thank you. I'm happy to take questions.
