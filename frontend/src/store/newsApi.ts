import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { NewsEvent, NewsArticle } from '../types'

export const newsApi = createApi({
  reducerPath: 'newsApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  tagTypes: ['Events', 'Articles'],
  endpoints: (builder) => ({
    getTop5Events: builder.query<{ events: NewsEvent[] }, void>({
      query: () => '/news/top5',
      providesTags: ['Events'],
      keepUnusedDataFor: 600, // 10 min cache — no re-fetch on every mount
    }),
    getArticles: builder.query<{ articles: NewsArticle[] }, number>({
      query: (limit = 50) => `/news/articles?limit=${limit}`,
      providesTags: ['Articles'],
      keepUnusedDataFor: 600,
    }),
    refreshNews: builder.mutation<void, void>({
      query: () => ({ url: '/news/refresh', method: 'POST' }),
      invalidatesTags: ['Events', 'Articles'], // cache bust only on manual refresh
    }),
  }),
})

export const { useGetTop5EventsQuery, useGetArticlesQuery, useRefreshNewsMutation } = newsApi
