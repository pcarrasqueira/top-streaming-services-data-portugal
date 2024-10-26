# FlixPatrol to Trakt List Sync

This repository contains a Python script that scrapes the top 10 movies and TV shows from [FlixPatrol](https://flixpatrol.com/top10/netflix/portugal/) and syncs them to your Trakt account by creating and updating Trakt lists.

## Features

- Scrapes the top 10 movies and TV shows from Netflix in Portugal on FlixPatrol.
- Creates or updates Trakt lists for these top movies and TV shows.
- Runs automatically on a daily schedule using GitHub Actions.

## Requirements

To run this project, you'll need:

- **Python 3.x** installed
- A **Trakt API key** and **OAuth tokens** (see [Trakt API documentation](https://trakt.docs.apiary.io/) for details on how to get this)
  