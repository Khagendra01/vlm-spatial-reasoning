import json

d = json.load(open('results/equiorient/pilot_run_v2_final_matrix.json',
                   encoding='utf-8'))
print('lambda_selected:', d['lambda_selected'])
for arm in ['augmentation_only', 'output_consistency', 'latent_invariance',
            'equiorient', 'wrong_geometry_equiorient']:
    a = d['per_arm_val'][arm]
    rp = a['rho_per_transform']
    print(f"{arm:24s} val {a['val_acc']:.4f} | holdout {a['holdout_VoH_accuracy']:.4f} "
          f"| zcorr {a['holdout_VoH_accuracy_z_corrupted']:.4f} "
          f"| latent_VH {a['latent_equivariance_error_VoH']:.4f} "
          f"| probe {a['depth_probe_holdout_acc']:.4f} zd {a['depth_probe_z_d_holdout_acc']:.4f}")
    print(f"{'':24s}   rhoH {rp['correct']['hflip']:.4f} rhoV {rp['correct']['vflip']:.4f} "
          f"rhoVH {rp['correct']['v_after_h']:.4f} | "
          f"wrongH {rp['wrong']['hflip']:.4f} wrongV {rp['wrong']['vflip']:.4f} "
          f"wrongVH {rp['wrong']['v_after_h']:.4f}")
    tl = a['train_loss']
    print(f"{'':24s}   ans {tl['answer']} struct {tl['structural']}")
