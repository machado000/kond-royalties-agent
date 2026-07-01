#!/bin/bash

SOURCE_PROJECT="g-analytics-487213"
SOURCE_DATASET="analytics_253977277"
DEST_PROJECT="mistral-analytics"
DEST_DATASET="analytics_253977277"
# START_DATE="20260601"
START_DATE=$(gdate -d "7 days ago" +%Y%m%d)
END_DATE=$(gdate -d "yesterday" +%Y%m%d)


# GA4 events_* daily tables: copy date range, skip tables that already exist at destination
echo "--- GA4 events_* (raw daily, $START_DATE to $END_DATE) ---"
current=$START_DATE
while [ "$current" -le "$END_DATE" ]; do
  table="events_$current"
  if bq show "$DEST_PROJECT:$DEST_DATASET.$table" >/dev/null 2>&1; then
    echo "Skipping $table (already exists)"
  else
    echo ""
    echo "Copying $table..."
    bq cp "$SOURCE_PROJECT:$SOURCE_DATASET.$table" "$DEST_PROJECT:$DEST_DATASET.$table"
  fi
  current=$(gdate -d "$current + 1 day" +%Y%m%d)
done

# GA4 bronze tables
for table in ga4_dim_session_traffic ga4_events_click ga4_events_ecommerce ga4_events_pageview ga4_events_sessionstart ga4_events_submit; do
  echo ""
  echo "Copying '$table'..."
  bq cp --force --project_id=g-analytics-487213 "g-analytics-487213:bronze_us.$table" "mistral-analytics:ga4_bronze.$table"
done


# GA4 silver tables
for table in ga4_clicks ga4_ecommerce ga4_general_traffic ga4_pageviews; do
  echo ""
  echo "Copying '$table'..."
  bq cp --force --project_id=g-analytics-487213 "g-analytics-487213:silver_us.$table" "mistral-analytics:ga4_silver.$table"
done


# Google Ads bronze tables
for table in p_ads_ad_group_ad_8784814486 p_ads_asset_group_8784814486 p_ads_conversion_action_8784814486 p_ads_keyword_view_8784814486 p_ads_search_term_view_8784814486 p_ads_video_8784814486; do
  echo ""
  echo "Copying '$table'..."
  bq cp --force --project_id=gads-487211 "gads-487211:bronze_us.$table" "mistral-analytics:google_ads.$table"
done


# Meta Ads bronze tables
for table in fb_ad_accounts fb_ad_insights fb_ad_summary fb_adsets fb_campaigns; do
  echo ""
  echo "Copying '$table'..."
  bq cp --force --project_id=facebook-ads-487216 "facebook-ads-487216:bronze.$table" "mistral-analytics:facebook_ads_bronze.$table"
done


# Meta Ads silver tables
for table in fb_ad_insights fb_ad_summary fb_adsets fb_campaigns; do
  echo ""
  echo "Copying '$table'..."
  bq cp --force --project_id=facebook-ads-487216 "facebook-ads-487216:silver.$table" "mistral-analytics:facebook_ads_silver.$table"
done

echo "--- Sync complete ---"
