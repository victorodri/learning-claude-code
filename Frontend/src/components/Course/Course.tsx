"use client";

import { useState } from "react";
import Image from "next/image";
import styles from "./Course.module.scss";
import { Course as CourseType } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";

type CourseProps = Omit<CourseType, "slug">;

const FALLBACK_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='420' height='260' viewBox='0 0 420 260'%3E%3Crect fill='%23f0f0f0' width='420' height='260'/%3E%3Ctext fill='%23999' font-family='system-ui' font-size='18' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3ECurso%3C/text%3E%3C/svg%3E";

export const Course = ({
  id,
  name,
  description,
  thumbnail,
  average_rating,
  total_ratings
}: CourseProps) => {
  const [imgSrc, setImgSrc] = useState(thumbnail);
  const [hasError, setHasError] = useState(false);

  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        {hasError ? (
          <div className={styles.fallbackImage}>
            <span>{name.charAt(0)}</span>
          </div>
        ) : (
          <Image
            src={imgSrc}
            alt={name}
            width={420}
            height={260}
            className={styles.thumbnail}
            onError={() => {
              setImgSrc(FALLBACK_IMAGE);
              setHasError(true);
            }}
            priority={false}
          />
        )}
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{name}</h2>
        <p className={styles.description}>{description}</p>

        {typeof average_rating === 'number' && (
          <div className={styles.ratingContainer}>
            <StarRating
              rating={average_rating}
              totalRatings={total_ratings}
              showCount={true}
              size="small"
              readonly={true}
            />
          </div>
        )}
      </div>
    </article>
  );
};
