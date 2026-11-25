# Expectativas anteriores que cambia ADR-0014, enmienda 1

## test_presentation_advances_inside_the_observed_window

Consultaba a +5 y +25 s y exigía avance. En esta parada, sin estado del operador, §4.6 exige esperar 30 s. Consulta ahora a +35 y +55 s, todavía dentro de la ventana observada de 60 s. Conserva las aserciones de modo, método, avance y timestamps del ancla.

## test_stale_frozen_freezes_at_the_anchor_without_envelope

Exigía que un movimiento ya caducado volviera al ancla. §4.4 F1 exige igualdad con el progreso al caducar. Se comprueba ese progreso, su diferencia positiva respecto del ancla y la identidad de la última posición confirmada. Se conservan modo stale, método, ausencia de envolvente y vigencia, e instante confirmado.

## test_horizon_exhausted_freezes_even_with_a_fresh_anchor

Exigía volver al ancla al dibujar después del horizonte de un movimiento fresco. §4.4 F1 exige igualdad con el final autorizado incluso cuando solo cambia el reloj de presentación. Se comprueban el avance autorizado, la base de congelación y el progreso confirmado. Se conservan método y motivo de horizonte.

## test_interpolated_only_between_two_real_anchors

El fotograma en directo a +5 s exigía avance. §4.6 aplica la espera mínima a esta muestra en zona con estado ausente. Se consulta a +35 s para comprobar el avance y a +29,999 s para comprobar progreso idéntico al ancla. Se conservan las tres aserciones de interpolación y la de avance en directo.

## test_gps_recovery_after_estimation_keeps_raw_matched_and_rendered_distinct

La recuperación cercana se generaba a 40 m por delante de la estimación del motor. Ahora se genera a 40 m de la estimación presentada. La espera R8 (§4.6) separa ambas magnitudes. Se conserva la fixture, el límite de 70 m y cada aserción de identidad, procedencia, método y monotonía. El caso independiente RecoveryMeasurement mide el salto con el GPS original, sin aplicar aquel límite. Resultado sintético 311,371489 m. El salto en vivo sigue UNVERIFIED hasta MP-025b (p50 ≤ 200 m con al menos 500 pares).
