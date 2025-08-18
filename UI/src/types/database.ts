export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.3 (519615d)"
  }
  public: {
    Tables: {
      articles: {
        Row: {
          author: string | null
          categories: string[] | null
          content: string
          duplicate_of: string | null
          embedding: string | null
          fetched_at: string
          id: string
          is_duplicate: boolean
          key_points: string[] | null
          published_at: string
          relevance_score: number | null
          source: Database["public"]["Enums"]["article_source"]
          source_id: string
          summary: string | null
          title: string
          url: string
        }
        Insert: {
          author?: string | null
          categories?: string[] | null
          content: string
          duplicate_of?: string | null
          embedding?: string | null
          fetched_at?: string
          id?: string
          is_duplicate?: boolean
          key_points?: string[] | null
          published_at: string
          relevance_score?: number | null
          source: Database["public"]["Enums"]["article_source"]
          source_id: string
          summary?: string | null
          title: string
          url: string
        }
        Update: {
          author?: string | null
          categories?: string[] | null
          content?: string
          duplicate_of?: string | null
          embedding?: string | null
          fetched_at?: string
          id?: string
          is_duplicate?: boolean
          key_points?: string[] | null
          published_at?: string
          relevance_score?: number | null
          source?: Database["public"]["Enums"]["article_source"]
          source_id?: string
          summary?: string | null
          title?: string
          url?: string
        }
        Relationships: [
          {
            foreignKeyName: "articles_duplicate_of_fkey"
            columns: ["duplicate_of"]
            isOneToOne: false
            referencedRelation: "articles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "articles_duplicate_of_fkey"
            columns: ["duplicate_of"]
            isOneToOne: false
            referencedRelation: "articles_view"
            referencedColumns: ["id"]
          },
        ]
      }
      audio_processing_queue: {
        Row: {
          created_at: string | null
          digest_id: string | null
          error_message: string | null
          id: number
          processed_at: string | null
          retry_count: number | null
          status: string | null
        }
        Insert: {
          created_at?: string | null
          digest_id?: string | null
          error_message?: string | null
          id?: number
          processed_at?: string | null
          retry_count?: number | null
          status?: string | null
        }
        Update: {
          created_at?: string | null
          digest_id?: string | null
          error_message?: string | null
          id?: number
          processed_at?: string | null
          retry_count?: number | null
          status?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "audio_processing_queue_digest_id_fkey"
            columns: ["digest_id"]
            isOneToOne: false
            referencedRelation: "daily_digests"
            referencedColumns: ["id"]
          },
        ]
      }
      daily_digests: {
        Row: {
          audio_duration: number | null
          audio_generated_at: string | null
          audio_size: number | null
          audio_url: string | null
          created_at: string
          digest_date: string
          id: string
          summary_text: string
          total_articles_processed: number
          voice_type: string | null
        }
        Insert: {
          audio_duration?: number | null
          audio_generated_at?: string | null
          audio_size?: number | null
          audio_url?: string | null
          created_at?: string
          digest_date: string
          id?: string
          summary_text: string
          total_articles_processed: number
          voice_type?: string | null
        }
        Update: {
          audio_duration?: number | null
          audio_generated_at?: string | null
          audio_size?: number | null
          audio_url?: string | null
          created_at?: string
          digest_date?: string
          id?: string
          summary_text?: string
          total_articles_processed?: number
          voice_type?: string | null
        }
        Relationships: []
      }
      digest_articles: {
        Row: {
          article_id: string
          digest_id: string
        }
        Insert: {
          article_id: string
          digest_id: string
        }
        Update: {
          article_id?: string
          digest_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "digest_articles_article_id_fkey"
            columns: ["article_id"]
            isOneToOne: false
            referencedRelation: "articles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "digest_articles_article_id_fkey"
            columns: ["article_id"]
            isOneToOne: false
            referencedRelation: "articles_view"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "digest_articles_digest_id_fkey"
            columns: ["digest_id"]
            isOneToOne: false
            referencedRelation: "daily_digests"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      articles_view: {
        Row: {
          author: string | null
          categories_text: string | null
          content: string | null
          duplicate_of: string | null
          fetched_at: string | null
          id: string | null
          is_duplicate: boolean | null
          key_points_text: string | null
          published_at: string | null
          relevance_score: number | null
          source: Database["public"]["Enums"]["article_source"] | null
          source_id: string | null
          summary: string | null
          title: string | null
          url: string | null
        }
        Insert: {
          author?: string | null
          categories_text?: never
          content?: string | null
          duplicate_of?: string | null
          fetched_at?: string | null
          id?: string | null
          is_duplicate?: boolean | null
          key_points_text?: never
          published_at?: string | null
          relevance_score?: number | null
          source?: Database["public"]["Enums"]["article_source"] | null
          source_id?: string | null
          summary?: string | null
          title?: string | null
          url?: string | null
        }
        Update: {
          author?: string | null
          categories_text?: never
          content?: string | null
          duplicate_of?: string | null
          fetched_at?: string | null
          id?: string | null
          is_duplicate?: boolean | null
          key_points_text?: never
          published_at?: string | null
          relevance_score?: number | null
          source?: Database["public"]["Enums"]["article_source"] | null
          source_id?: string | null
          summary?: string | null
          title?: string | null
          url?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "articles_duplicate_of_fkey"
            columns: ["duplicate_of"]
            isOneToOne: false
            referencedRelation: "articles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "articles_duplicate_of_fkey"
            columns: ["duplicate_of"]
            isOneToOne: false
            referencedRelation: "articles_view"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Functions: {
      binary_quantize: {
        Args: { "": string } | { "": unknown }
        Returns: unknown
      }
      get_top_articles_for_digest: {
        Args: { article_limit?: number; since_date?: string }
        Returns: {
          id: string
          published_at: string
          relevance_score: number
          source: Database["public"]["Enums"]["article_source"]
          summary: string
          title: string
          url: string
        }[]
      }
      halfvec_avg: {
        Args: { "": number[] }
        Returns: unknown
      }
      halfvec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      halfvec_send: {
        Args: { "": unknown }
        Returns: string
      }
      halfvec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      hnsw_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_sparsevec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnswhandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflat_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflat_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflathandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      l2_norm: {
        Args: { "": unknown } | { "": unknown }
        Returns: number
      }
      l2_normalize: {
        Args: { "": string } | { "": unknown } | { "": unknown }
        Returns: unknown
      }
      match_articles: {
        Args: {
          match_count?: number
          match_threshold?: number
          query_embedding: string
        }
        Returns: {
          id: string
          published_at: string
          similarity: number
          title: string
          url: string
        }[]
      }
      sparsevec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      sparsevec_send: {
        Args: { "": unknown }
        Returns: string
      }
      sparsevec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      vector_avg: {
        Args: { "": number[] }
        Returns: string
      }
      vector_dims: {
        Args: { "": string } | { "": unknown }
        Returns: number
      }
      vector_norm: {
        Args: { "": string }
        Returns: number
      }
      vector_out: {
        Args: { "": string }
        Returns: unknown
      }
      vector_send: {
        Args: { "": string }
        Returns: string
      }
      vector_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
    }
    Enums: {
      article_source: "arxiv" | "hackernews" | "rss"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      article_source: ["arxiv", "hackernews", "rss"],
    },
  },
} as const